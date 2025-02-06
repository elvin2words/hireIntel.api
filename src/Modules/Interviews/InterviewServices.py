# interview_scheduler_service.py
import json
from datetime import datetime
from typing import List, Dict, Any, TypedDict, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from marshmallow import Schema, fields, validates, ValidationError
from src.Helpers.ErrorHandling import CustomError
from src.Helpers.LLMService import LLMService
from src.Modules.Interviews.InterviewDTOs import InterviewScheduleDTO
from src.Modules.Interviews.InterviewModels import InterviewSchedule, EmailNotification, InterviewStatus
from src.Modules.Interviews.InterviewRepository import InterviewScheduleRepository, EmailNotificationRepository
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationService import CandidateProfileDataService


class InterviewScheduleRequestSchema(Schema):
    candidate_ids = fields.List(fields.Str(required=True), required=True)
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)

    @validates('start_date')
    def validate_start_date(self, value):
        if value < datetime.now():
            raise ValidationError('start_date cannot be in the past')

    @validates('end_date')
    def validate_end_date(self, value):
        start_date = self.context.get('start_date')
        if start_date and value <= start_date:
            raise ValidationError('end_date must be after start_date')

class ProcessCandidatesResponse(TypedDict):
    hired_candidates: List[str]
    rejected_candidates: List[str]
    schedules: List[Dict]  # Will contain InterviewScheduleDTO objects

class InterviewSchedulerService:
    def __init__(self):
        self.__interview_repo = InterviewScheduleRepository()
        self.__email_repo = EmailNotificationRepository()
        self.__candidate_service = CandidateService()
        self.__llm_service = LLMService()
        self.__request_schema = InterviewScheduleRequestSchema()
        self.__candidate_profile = CandidateProfileDataService()

        # Initialize Jinja2 environment for email templates
        template_dir = Path(__file__).parent.parent.parent / 'static' / 'email_templates'
        self.__jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )


    def process_candidates(self, request_data: Dict[str, Any]) -> ProcessCandidatesResponse:
        """
        Process candidates for interview scheduling

        Returns:
        ProcessCandidatesResponse:
            hired_candidates: List[str] - List of hired candidate IDs
            rejected_candidates: List[str] - List of rejected candidate IDs
            schedules: List[InterviewScheduleDTO] - List of interview schedule DTOs
        """
        try:
            # Validate request data
            validated_data = self.__request_schema.load(request_data)

            # Convert string dates to datetime if they aren't already
            if isinstance(validated_data['start_date'], str):
                validated_data['start_date'] = datetime.fromisoformat(validated_data['start_date'])
            if isinstance(validated_data['end_date'], str):
                validated_data['end_date'] = datetime.fromisoformat(validated_data['end_date'])

            hired_candidates = []
            rejected_candidates = []

            # Categorize candidates based on status
            for candidate_id in validated_data['candidate_ids']:
                candidate = self.__candidate_service.fetch_by_id(candidate_id)
                if not candidate:
                    raise CustomError(f"Candidate not found: {candidate_id}", 404)

                if candidate.get('status') == 'HIRED':
                    hired_candidates.append(candidate)
                elif candidate.get('status') == 'REJECTED':
                    rejected_candidates.append(candidate)

            response: ProcessCandidatesResponse = {
                'hired_candidates': [c.get('id') for c in hired_candidates],
                'rejected_candidates': [c.get('id') for c in rejected_candidates],
                'schedules': []
            }

            # Process hired candidates
            if hired_candidates:
                # Schedule interviews
                schedules = self._schedule_interviews(
                    hired_candidates,
                    validated_data['start_date'],
                    validated_data['end_date']
                )

                # Send acceptance emails
                self._send_acceptance_emails(hired_candidates, schedules)

                # Convert schedules to DTOs
                schedule_schema = InterviewScheduleDTO(many=True)
                response['schedules'] = schedule_schema.dump(schedules)

            # Process rejected candidates
            if rejected_candidates:
                self._send_rejection_emails(rejected_candidates)

            return response

        except ValidationError as e:
            raise CustomError(f"Invalid request data: {e.messages}", 400)
        except Exception as e:
            raise CustomError(str(e), 400)

    def get_all_schedules(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get all interview schedules with optional filtering

        Args:
            filters (Dict): Optional filters for querying schedules
                Supported filters:
                - status: InterviewStatus
                - start_date: datetime
                - end_date: datetime
                - candidate_id: str

        Returns:
            List[Dict]: List of interview schedule DTOs
        """
        try:
            # Process date filters if present
            if filters and ('start_date' in filters or 'end_date' in filters):
                filters['start_date'] = datetime.fromisoformat(
                    filters['start_date']) if 'start_date' in filters else None
                filters['end_date'] = datetime.fromisoformat(filters['end_date']) if 'end_date' in filters else None

            # Get schedules from repository
            schedules = self.__interview_repo.get_with_filters(filters or {})

            # Convert to DTOs
            schedule_schema = InterviewScheduleDTO(many=True)
            return schedule_schema.dump(schedules)

        except Exception as e:
            raise CustomError(f"Failed to fetch interview schedules: {str(e)}", 400)

    def get_schedule_by_id(self, schedule_id: str) -> Dict:
        """
        Get a specific interview schedule by ID

        Args:
            schedule_id (str): The ID of the interview schedule

        Returns:
            Dict: Interview schedule DTO
        """
        try:
            schedule = self.__interview_repo.get_by_id(schedule_id)
            if not schedule:
                raise CustomError(f"Interview schedule not found: {schedule_id}", 404)

            schedule_schema = InterviewScheduleDTO()
            return schedule_schema.dump(schedule)

        except Exception as e:
            raise CustomError(f"Failed to fetch interview schedule: {str(e)}", 400)

    def update_schedule(self, schedule_id: str, data: Dict) -> Dict:
        """
        Update an existing interview schedule

        Args:
            schedule_id (str): The ID of the interview schedule to update
            data (Dict): Updated schedule data
        """
        try:
            # Validate the schedule exists
            schedule = self.__interview_repo.get_by_id(schedule_id)
            if not schedule:
                raise CustomError(f"Interview schedule not found: {schedule_id}", 404)

            # Validate datetime updates
            if 'start_datetime' in data:
                start_datetime = datetime.fromisoformat(data['start_datetime'])
                if start_datetime < datetime.now():
                    raise CustomError("start_datetime cannot be in the past", 400)
                schedule.start_datetime = start_datetime

            if 'end_datetime' in data:
                end_datetime = datetime.fromisoformat(data['end_datetime'])
                if end_datetime <= schedule.start_datetime:
                    raise CustomError("end_datetime must be after start_datetime", 400)
                schedule.end_datetime = end_datetime

            # Update other fields
            if 'location' in data:
                schedule.location = data['location']
            if 'notes' in data:
                schedule.notes = data['notes']

            # Save updates
            updated_schedule = self.__interview_repo.update(schedule)

            # Return DTO
            schedule_schema = InterviewScheduleDTO()
            return schedule_schema.dump(updated_schedule)

        except Exception as e:
            raise CustomError(f"Failed to update interview schedule: {str(e)}", 400)

    def cancel_schedule(self, schedule_id: str) -> Dict:
        """
        Cancel an interview schedule

        Args:
            schedule_id (str): The ID of the interview schedule to cancel
        """
        try:
            # Get and validate schedule
            schedule = self.__interview_repo.get_by_id(schedule_id)
            if not schedule:
                raise CustomError(f"Interview schedule not found: {schedule_id}", 404)

            if schedule.status == InterviewStatus.COMPLETED:
                raise CustomError("Cannot cancel a completed interview", 400)

            # Update status through repository
            cancelled_schedule = self.__interview_repo.update_status(
                schedule_id,
                InterviewStatus.CANCELLED
            )

            # Create cancellation notification
            notification_data = {
                'candidate_id': schedule.candidate_id,
                'subject': 'Interview Cancelled',
                'email_type': 'cancelled',
                'content': f'Your interview scheduled for {schedule.start_datetime.strftime("%B %d, %Y at %I:%M %p")} has been cancelled.'
            }
            self.__email_repo.create_notification(notification_data)

            # Return DTO
            schedule_schema = InterviewScheduleDTO()
            return schedule_schema.dump(cancelled_schedule)

        except Exception as e:
            raise CustomError(f"Failed to cancel interview schedule: {str(e)}", 400)

    def complete_schedule(self, schedule_id: str) -> Dict:
        """
        Mark an interview schedule as completed

        Args:
            schedule_id (str): The ID of the interview schedule to mark as completed
        """
        try:
            # Get and validate schedule
            schedule = self.__interview_repo.get_by_id(schedule_id)
            if not schedule:
                raise CustomError(f"Interview schedule not found: {schedule_id}", 404)

            if schedule.status != InterviewStatus.SCHEDULED:
                raise CustomError(f"Cannot complete interview with status: {schedule.status.value}", 400)

            if schedule.end_datetime > datetime.now():
                raise CustomError("Cannot complete an interview before its scheduled end time", 400)

            # Update status through repository
            completed_schedule = self.__interview_repo.update_status(
                schedule_id,
                InterviewStatus.COMPLETED
            )

            # Return DTO
            schedule_schema = InterviewScheduleDTO()
            return schedule_schema.dump(completed_schedule)

        except Exception as e:
            raise CustomError(f"Failed to complete interview schedule: {str(e)}", 400)

    def _schedule_interviews(self, candidates: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """Schedule interviews for candidates within the specified date range"""
        try:
            # Format dates
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Build candidate details list
            candidate_details = []
            for candidate in candidates:
                first_name = candidate.get('first_name', '')
                last_name = candidate.get('last_name', '')
                details = {
                    'id': candidate.get('id'),
                    'name': f"{first_name} {last_name}",
                    'position': candidate.get('position', 'Not specified')
                }
                candidate_details.append(details)

            # Convert to JSON string separately
            candidates_json = json.dumps(candidate_details, indent=2)

            # Build schedule prompt
            schedule_prompt = f"""
            Create an interview schedule for {len(candidates)} candidates with the following constraints:
            - Date Range: {start_date_str} to {end_date_str}
            - Business Hours: 9:00 AM to 5:00 PM
            - Maximum 4 interviews per day
            - 1 hour duration per interview
            - 1 hour break between interviews

            Candidate Details:
            {candidates_json}

            Return a schedule that follows this exact JSON structure:
            {{
                "schedule_id": str,
                "interviews": [
                    {{
                        "candidate_id": str,
                        "interviewer_id": str,
                        "start_datetime": str,
                        "end_datetime": str,
                        "duration_minutes": int,
                        "location": {{
                            "type": "virtual",
                            "details": "Online meeting link will be provided"
                        }},
                        "meeting_link": str,
                        "requirements": ["stable internet", "quiet environment"]
                    }}
                ],
                "constraints_satisfied": bool,
                "schedule_metadata": {{
                    "total_interviews": int,
                    "total_duration_hours": float,
                    "daily_distribution": {{
                        "YYYY-MM-DD": number_of_interviews
                    }}
                }}
            }}
            """

            # Get schedule from LLM
            schedule_response = self.__llm_service.create_interview_schedule(schedule_prompt)

            if not schedule_response['constraints_satisfied']:
                raise CustomError("Could not create schedule satisfying all constraints", 400)

            # Create interview schedules
            created_schedules = []
            for interview in schedule_response['interviews']:
                interview_schedule = InterviewSchedule(
                    candidate_id=interview['candidate_id'],
                    interviewer_id=interview['interviewer_id'],
                    start_datetime=datetime.fromisoformat(interview['start_datetime']),
                    end_datetime=datetime.fromisoformat(interview['end_datetime']),
                    status=InterviewStatus.SCHEDULED,
                    location=interview['location']['type'],
                    meeting_link=interview.get('meeting_link')
                )
                created_schedule = self.__interview_repo.create(interview_schedule)
                created_schedules.append(created_schedule)

            return created_schedules

        except Exception as e:
            error_msg = "Failed to schedule interviews: {}".format(str(e))
            raise CustomError(error_msg, 400)


    def _process_profile_data(self, candidate_id: str) -> dict:
        """Process and format candidate profile data for email generation"""
        profile_data = self.__candidate_profile.get_profile_by_candidate_id(candidate_id)
        if not profile_data or not profile_data.get('matches'):
            raise CustomError("No profile match found for candidate", 400)

        latest_match = profile_data['matches'][-1]

        # Process technical skills
        tech_skills = latest_match.get('technicalSkills', {})
        strong_skills = []
        improvement_areas = []
        missing_skills = []

        for skill in tech_skills.get('skillMatches', []):
            skill_name = skill.get('skill', '')
            job_rel = skill.get('job_relevance', 0)
            prof = skill.get('candidate_proficiency', 0)

            if job_rel > 0.7:
                if prof > 0.7:
                    strong_skills.append(skill_name)
                elif prof < 0.4:
                    missing_skills.append(skill_name)
                else:
                    improvement_areas.append(skill_name)

        # Process experience data
        experience = latest_match.get('experience', {})
        industry_exp = []
        for exp in experience.get('industryExperience', []):
            industry_exp.append({
                'industry': exp.get('industry', ''),
                'years': exp.get('years', 0)
            })

        relevant_roles = []
        for role in experience.get('relevantRoles', []):
            relevant_roles.append({
                'title': role.get('title', ''),
                'company': role.get('company', ''),
                'duration': role.get('duration', 0)
            })

        # Process projects
        projects = latest_match.get('projects', {})
        relevant_projects = []
        for proj in projects.get('items', []):
            if proj.get('relevance', 0) > 0.6:
                relevant_projects.append({
                    'name': proj.get('name', ''),
                    'relevance': proj.get('relevance', 0)
                })

        # Process social presence
        social = latest_match.get('socialPresence', {})

        return {
            'overall_score': latest_match.get('overall_match_score', 0),
            'technical_skills': {
                'score': tech_skills.get('score', 0),
                'strong_skills': strong_skills,
                'improvement_areas': improvement_areas,
                'missing_skills': missing_skills
            },
            'experience': {
                'score': experience.get('score', 0),
                'years': experience.get('years_of_experience', 0),
                'industry_experience': industry_exp,
                'relevant_roles': relevant_roles
            },
            'education': {
                'score': latest_match.get('education', {}).get('score', 0),
                'degrees': latest_match.get('education', {}).get('degrees', [])
            },
            'projects': {
                'score': projects.get('score', 0),
                'relevant_projects': relevant_projects
            },
            'social_presence': {
                'score': social.get('score', 0),
                'linkedin': social.get('linkedin_activity_score', 0),
                'github': social.get('github_contribution_score', 0),
                'blog': social.get('blog_post_score', 0)
            }
        }


    def _format_interview_details(self, schedule: Dict) -> dict:
        """Format interview schedule details"""
        start_time = schedule.get('start_datetime')
        interview_date = "TBD"
        interview_time = "TBD"

        if start_time:
            interview_date = start_time.strftime('%B %d, %Y')
            interview_time = start_time.strftime('%I:%M %p')

        return {
            'date': interview_date,
            'time': interview_time,
            'location': schedule.get('location', 'Virtual'),
            'confirmation_link': "https://your-domain.com/confirm-interview/{}".format(schedule.get('id', ''))
        }


    def _send_email(self, template_name: str, email_data: Dict, notification_type: str) -> None:
        """Send email using template and data"""
        template = self.__jinja_env.get_template(template_name)
        email_content = template.render(**email_data)

        email = EmailNotification(
            candidate_id=email_data.get('candidate_id'),
            email_type=notification_type,
            subject=email_data.get('subject'),
            content=email_content
        )
        self.__email_repo.create(email)


    def _send_acceptance_emails(self, candidates: List[Dict], schedules: List[Dict]) -> None:
        """Send acceptance emails to hired candidates with their interview schedules"""
        for candidate in candidates:
            try:
                # Get basic candidate info
                first_name = candidate.get('first_name', '')
                last_name = candidate.get('last_name', '')
                candidate_name = f"{first_name} {last_name}"
                position = candidate.get('position', 'the position')

                # Get schedule
                schedule = next(
                    (s for s in schedules if s.get('candidate_id') == candidate.get('id')),
                    None
                )
                if not schedule:
                    raise CustomError(f"No schedule found for candidate {candidate_name}", 400)

                # Get profile analysis and interview details
                profile_data = self._process_profile_data(candidate.get('id'))
                interview_details = self._format_interview_details(schedule)

                # Format skills and achievements for the prompt
                strong_skills_str = ', '.join(profile_data['technical_skills']['strong_skills']) or 'technical expertise'
                projects_str = ', '.join(
                    [p['name'] for p in profile_data['projects']['relevant_projects']]) or 'impressive project portfolio'

                email_prompt = f"""
                Create an enthusiastic and welcoming acceptance email for a candidate who has been selected for an interview.
                Highlight their specific strengths and qualifications that led to their selection.
    
                Candidate Details:
                - Name: {candidate_name}
                - Position: {position}
                - Overall Match Score: {profile_data['overall_score']}
                - Key Technical Skills: {strong_skills_str}
                - Years of Experience: {profile_data['experience']['years']}
                - Notable Projects: {projects_str}
    
                Interview Details:
                - Date: {interview_details['date']}
                - Time: {interview_details['time']}
                - Location: {interview_details['location']}
    
                Guidelines for Response:
                1. Start with warm congratulations and excitement about their potential
                2. Specifically mention their strong technical skills and experience that impressed us
                3. Reference their years of experience and relevant project work
                4. Include clear interview details and next steps
                5. Maintain an enthusiastic and welcoming tone throughout
                6. End with clear instructions about interview preparation and confirmation
    
                {self._get_acceptance_json_structure()}
                """

                email_response = self.__llm_service.create_notification(email_prompt)

                # Prepare and send email
                template_data = {
                    'candidate_id': candidate.get('id'),
                    'candidate_name': email_response['personalization']['candidate_name'],
                    'subject': email_response['subject'],
                    'email_content': email_response['content'],
                    'interview_details': interview_details,
                    'key_strengths': email_response['personalization']['custom_fields']['key_strengths'],
                    'preparation_tips': email_response['personalization']['custom_fields']['preparation_tips']
                }

                self._send_email('acceptance.html', template_data, 'accepted')

            except Exception as e:
                error_msg = "Failed to send acceptance email: {}".format(str(e))
                raise CustomError(error_msg, 400)


    def _send_rejection_emails(self, candidates: List[Dict]) -> None:
        """Send rejection emails to candidates who weren't selected"""
        for candidate in candidates:
            try:
                # Get basic candidate info
                first_name = candidate.get('first_name', '')
                last_name = candidate.get('last_name', '')
                candidate_name = f"{first_name} {last_name}"
                position = candidate.get('position', 'the position')

                # Get profile analysis
                profile_data = self._process_profile_data(candidate.get('id'))

                email_prompt = f"""
                Create a personalized, constructive, and actionable rejection email for a job candidate.
                Focus on providing specific feedback and growth opportunities based on their profile analysis.
    
                Candidate Details:
                - Name: {candidate_name}
                - Position: {position}
                - Overall Match Score: {profile_data['overall_score']}
    
                Technical Skills Analysis:
                - Score: {profile_data['technical_skills']['score']}
                - Areas for Improvement: {', '.join(profile_data['technical_skills']['improvement_areas'])}
                - Missing Critical Skills: {', '.join(profile_data['technical_skills']['missing_skills'])}
    
                Experience Analysis:
                - Score: {profile_data['experience']['score']}
                - Years of Experience: {profile_data['experience']['years']}
    
                Professional Presence:
                - Overall Score: {profile_data['social_presence']['score']}
                - LinkedIn Activity: {profile_data['social_presence']['linkedin']}
                - GitHub Contributions: {profile_data['social_presence']['github']}
    
                Guidelines for Response:
                1. Start with a warm, personal greeting
                2. Provide constructive feedback on areas of improvement
                3. Include specific recommendations for skill development
                4. Maintain an encouraging tone
                5. End with future opportunities
    
                {self._get_rejection_json_structure()}
                """

                email_response = self.__llm_service.create_notification(email_prompt)

                # Prepare and send email
                template_data = {
                    'candidate_id': candidate.get('id'),
                    'candidate_name': email_response['personalization']['candidate_name'],
                    'subject': email_response['subject'],
                    'email_content': email_response['content'],
                    'feedback': email_response['personalization']['custom_fields']['feedback']
                }

                self._send_email('rejection.html', template_data, 'rejected')

            except Exception as e:
                error_msg = "Failed to send rejection email: {}".format(str(e))
                raise CustomError(error_msg, 400)


    def _get_acceptance_json_structure(self) -> str:
        """Return the JSON structure for acceptance emails"""
        return """
        Return a notification object with this exact JSON structure:
        {
            "subject": str,
            "content": str,
            "notification_type": "acceptance",
            "personalization": {
                "candidate_name": str,
                "custom_fields": {
                    "interview_date": str,
                    "interview_time": str,
                    "interview_location": str,
                    "key_strengths": List[str],
                    "preparation_tips": List[str]
                }
            },
            "metadata": {
                "priority": "high",
                "send_time": "ISO datetime string"
            }
        }
        """


    def _get_rejection_json_structure(self) -> str:
        """Return the JSON structure for rejection emails"""
        return """
        Return a notification object with this exact JSON structure:
        {
            "subject": str,
            "content": str,
            "notification_type": "rejection",
            "personalization": {
                "candidate_name": str,
                "custom_fields": {
                    "position": str,
                    "feedback": {
                        "main_reasons": List[str],
                        "technical_gaps": {
                            "missing_skills": List[str],
                            "improvement_areas": List[str]
                        },
                        "experience_feedback": {
                            "strengths": List[str],
                            "gaps": List[str]
                        },
                        "portfolio_feedback": str,
                        "professional_presence": {
                            "strengths": List[str],
                            "improvement_tips": List[str]
                        },
                        "action_items": List[str]
                    }
                }
            },
            "metadata": {
                "priority": "medium",
                "send_time": "ISO datetime string"
            }
        }
        """