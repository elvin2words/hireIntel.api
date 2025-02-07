# interview_scheduler_service.py
import json
from datetime import datetime
from typing import List, Dict, Any, TypedDict, Optional
from marshmallow import Schema, fields, validates, ValidationError
from src.Helpers.ErrorHandling import CustomError
from src.Helpers.LLMService import LLMService
from src.Modules.Interviews.InterviewDTOs import InterviewScheduleDTO
from src.Modules.Interviews.InterviewModels import InterviewSchedule, InterviewStatus
from src.Modules.Interviews.InterviewNotificationService import InterviewNotificationService, NotificationType
from src.Modules.Interviews.InterviewRepository import InterviewScheduleRepository, EmailNotificationRepository
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationService import CandidateProfileDataService


class InterviewScheduleRequestSchema(Schema):
    accepted_candidate_ids = fields.List(fields.Str(required=True), required=True)
    rejected_candidate_ids = fields.List(fields.Str(required=True), required=True)
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
        self.__notificationService = InterviewNotificationService()


    #Todo: make it so that the meeting link is configured on the database front end
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

            if 'accepted_candidate_ids' in validated_data:
                # Categorize candidates based on status
                for candidate_id in validated_data['accepted_candidate_ids']:
                    candidate = self.__candidate_service.fetch_by_id(candidate_id)
                    if not candidate:
                        raise CustomError(f"Candidate not found: {candidate_id}", 404)
                    hired_candidates.append(candidate)

            if 'rejected_candidate_ids' in validated_data:
                for candidate_id in validated_data['rejected_candidate_ids']:
                    candidate = self.__candidate_service.fetch_by_id(candidate_id)
                    if not candidate:
                        raise CustomError(f"Candidate not found: {candidate_id}", 404)
                    rejected_candidates.append(candidate)

            print("hired candidates: ", hired_candidates)
            print("rejected candidates: ", rejected_candidates)

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

            print(f"My schedules : {response['schedules']}")
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

    def _schedule_interviews(self, candidates: List[Dict], start_date: datetime, end_date: datetime) -> List[InterviewSchedule]:
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
                    'candidate_id': candidate.get('id'),
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
            - 2 hour duration per interview
            - 2 hour break between interviews
            - For candidate id make sure to use the exact candidate id given on candidate details
            - For interview id use system00
            
            Candidate Details:
            {candidates_json}

            Return a schedule that follows this exact JSON structure:
            {{
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
            created_schedules = [] #Todo : should handle the meta data in a different table
            for interview in schedule_response['interviews']:
                interview_schedule = InterviewSchedule(
                    candidate_id=interview['candidate_id'],
                    interviewer_id=interview['interviewer_id'],
                    start_datetime=datetime.fromisoformat(interview['start_datetime']),
                    end_datetime=datetime.fromisoformat(interview['end_datetime']),
                    status=InterviewStatus.SCHEDULED,
                    location=interview['location']['type'],
                    meeting_link="https://us02web.zoom.us/j/1234567890?pwd=a1b2C3dEfGhI4JKlMnOpQ" # Todo: example, real link should be configured
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

    @staticmethod
    def _format_interview_details(schedule: InterviewSchedule) -> dict:
        """Format interview schedule details from an InterviewSchedule object"""
        start_time = schedule.start_datetime
        interview_date = "TBD"
        interview_time = "TBD"

        if start_time:
            interview_date = start_time.strftime('%B %d, %Y')
            interview_time = start_time.strftime('%I:%M %p')

        return {
            'date': interview_date,
            'time': interview_time,
            'location': schedule.location,
            'confirmation_link': "https://us02web.zoom.us/j/1234567890?pwd=a1b2C3dEfGhI4JKlMnOpQ" # Todo: example, real link should be configured
        }


    def _send_acceptance_emails(self, candidates: List[Dict], schedules: List[InterviewSchedule]) -> None:
        """Send acceptance emails to hired candidates with their interview schedules"""
        for candidate in candidates:
            try:
                print("Inside send_acceptance_emails:")
                print(f"candidate: {candidate}")
                # Get basic candidate info
                first_name = candidate['firstName']
                last_name = candidate['lastName']
                candidate_name = f"{first_name} {last_name}"
                position = candidate['job']['title']

                print("My schedules are : {}".format(schedules))

                # Get schedule
                schedule = next(
                    (s for s in schedules if s.candidate_id == candidate['id']),
                    None
                )

                if not schedule:
                    raise CustomError(f"No schedule found for candidate {candidate_name}", 400)

                # Get profile analysis and interview details
                profile_data = self._process_profile_data(candidate["id"])
                interview_details = self._format_interview_details(schedule)

                print("This part worked well .... ")

                # Format skills and achievements for the prompt
                strong_skills_str = ', '.join(profile_data['technical_skills']['strong_skills']) or 'technical expertise'
                projects_str = ', '.join(
                    [p['name'] for p in profile_data['projects']['relevant_projects']]) or 'impressive project portfolio'

                email_prompt = f"""
                                Create a friendly and professional interview invitation email. The tone should be warm but not overly formal.
                
                                Candidate Details:
                                - Name: {candidate_name}
                                - Position: {position}
                                - Key Technical Skills: {strong_skills_str}
                                - Notable Projects: {projects_str} (highlight max 2 most impressive projects)
                
                                Interview Details:
                                - Date: {interview_details['date']}
                                - Time: {interview_details['time']}
                                - Location: {interview_details['location']}
                
                                Email Requirements:
                                1. Start directly with positive news about moving forward
                                2. Keep it brief and enthusiastic (2-3 short paragraphs)
                                3. Mention one specific impressive aspect (project or skill)
                                4. Clearly state interview details
                                5. No sign-offs (Regards/Best/etc.)
                                6. End with clear next steps about confirming attendance
                    
                                Must Exclude:
                                - Any form of salutation or greeting
                                - Make sure not to put Any sign-off or closing phrases (Regards/Best/etc.)
                                - Placeholders or bracketed text
                                - Corporate phrases like "at this time" or "future endeavors"
                                - Generic statements about "applying again"
                                - Complex instructions
                    
                                Content Structure:
                                1. Start with excitement about their application
                                2. Mention one specific impressive thing about their profile
                                3. State interview details clearly
                                4. End with simple confirmation instructions
                    
                                Example Format:
                                "We're excited to move forward... [enthusiasm about their specific skill/project]
                                [clear interview details]
                                [simple confirmation request]"
                
                                {self._get_acceptance_json_structure()}
                                """

                print("Prompt created successfully")
                email_response = self.__llm_service.generate_notification_email(email_prompt)

                print("This is my email response: {}".format(email_response))

                # Prepare and send email
                template_data = {
                    'candidate_id': candidate["id"],
                    'candidate_name': email_response['personalization']['candidate_name'],
                    'subject': email_response['subject'],
                    'email_content': email_response['content'],
                    'interview_details': interview_details,
                    'key_strengths': email_response['personalization']['custom_fields']['key_strengths'],
                    'preparation_tips': email_response['personalization']['custom_fields']['preparation_tips']
                }

                print("template_data: {}".format(template_data))
                # self._send_email('acceptance.html', template_data, 'accepted')

                # Create and send notification
                self.__notificationService.create_notification(
                    candidate=candidate,
                    notification_data=template_data,
                    notification_type=NotificationType.ACCEPTANCE
                )

            except Exception as e:
                error_msg = "Failed to send acceptance email: {}".format(str(e))
                raise CustomError(error_msg, 400)

    def _send_rejection_emails(self, candidates: List[Dict]) -> None:
        """Send rejection emails to candidates who weren't selected"""
        for candidate in candidates:
            try:
                print("Inside send_rejection_emails:")
                print(f"candidate: {candidate}")

                # Get basic candidate info
                first_name = candidate['firstName']
                last_name = candidate['lastName']
                candidate_name = f"{first_name} {last_name}"
                position = candidate['job']['title']

                # Get profile analysis
                profile_data = self._process_profile_data(candidate["id"])

                # Get technical skills data
                tech_skills = profile_data['technical_skills']
                strong_skills = tech_skills.get('strong_skills', [])
                improvement_areas = tech_skills.get('improvement_areas', [])

                # Get project data
                projects = profile_data.get('projects', {}).get('relevant_projects', [])
                project_names = [p.get('name', '') for p in projects if p.get('relevance', 0) > 0.7]

                # Get experience data
                experience = profile_data.get('experience', {})
                years_exp = experience.get('years', 0)
                relevant_roles = experience.get('relevant_roles', [])

                # Format roles for content
                role_highlights = []
                for role in relevant_roles[:2]:  # Get top 2 most relevant roles
                    if role.get('title') and role.get('company'):
                        role_highlights.append(f"{role['title']} at {role['company']}")

                email_prompt = f"""
                Create a personal, genuine rejection email that sounds completely human. The email should be concise and warm.

                Candidate Profile:
                - Name: {candidate_name}
                - Position: {position}
                - Years of Experience: {years_exp}
                - Strong Technical Skills: {', '.join(strong_skills[:3])}
                - Notable Projects: {', '.join(project_names[:2])}
                - Relevant Roles: {', '.join(role_highlights)}
                - Areas for Development: {', '.join(improvement_areas[:2])}

                Essential Requirements:
                1. Write in a personal, conversational tone
                2. Keep it brief (3 paragraphs maximum)
                3. Reference one specific positive from their background (project/skill/role)
                5. Suggest exactly one area for growth
                6. Be direct but kind about the decision

                Must Exclude:
                - Placeholders or bracketed text
                - Make sure not to put Any sign-off or closing phrases (Regards/Best/etc.)
                - Abbreviations (use "for example" instead of "e.g.")
                - Corporate phrases like "at this time" or "future endeavors"
                - Mentions of "competitive process" or "other candidates"
                - Generic statements about "applying again"

                Structure:
                1. Thank them for applying to {position}
                2. State the decision clearly but kindly
                3. Highlight one specific impressive aspect
                4. Provide one specific growth suggestion

                {self._get_rejection_json_structure()}
                """

                print("Creating rejection email prompt...")
                email_response = self.__llm_service.generate_notification_email(email_prompt)

                print("Email response received:", email_response)

                # Prepare template data
                template_data = {
                    'candidate_id': candidate["id"],
                    'candidate_name': candidate_name,
                    'subject': "Update on Your Application",
                    'email_content': email_response['content'],
                    'feedback': {
                        'improvement_areas': improvement_areas,
                        'strong_skills': strong_skills,
                        'experience_feedback': f"{years_exp} years of experience",
                        'projects': project_names,
                        'roles': role_highlights
                    }
                }

                print("Sending rejection notification...")
                self.__notificationService.create_notification(
                    candidate=candidate,
                    notification_data=template_data,
                    notification_type=NotificationType.REJECTION
                )

            except Exception as e:
                error_msg = f"Failed to send rejection email to {candidate['firstName'], candidate['lastName']}: {str(e)}"
                print(f"Error in rejection email: {error_msg}")
                raise CustomError(error_msg, 400)


    @staticmethod
    def _get_acceptance_json_structure() -> str:
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


    @staticmethod
    def _get_rejection_json_structure() -> str:
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