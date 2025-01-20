import os
from datetime import datetime
import uuid
from enum import Enum

from src.Helpers.ErrorHandling import CustomError
from src.Helpers.MailService import MailService
from src.Modules.Interviews.InterviewDTOs import InterviewDTO
from src.Modules.Interviews.InterviewModels import Interview, InterviewStatus
from src.Modules.Interviews.InterviewRepository import InterviewRepository

class EmailType(Enum):
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"

class InterviewService:
    def __init__(self):
        self.__interview_repository = InterviewRepository()
        self.__mailService = MailService()

    def fetch_all(self, filters=None):
        try:
            interviews = self.__interview_repository.get_all_interviews(filters)
            if len(interviews) == 0:
                raise Exception("No interviews found")
            return InterviewDTO(many=True).dump(interviews)
        except Exception as e:
            raise CustomError(str(e), 400)

    def fetch_by_id(self, interview_id):
        try:
            interview = self.__interview_repository.get_interview_by_id(interview_id)
            if not interview:
                raise CustomError("Interview not found", 404)
            return InterviewDTO(many=False).dump(interview)
        except Exception as e:
            raise CustomError(str(e), 400)

    def schedule_interview(self, interview_data):
        try:
            # Check interviewer availability
            is_available = self.__interview_repository.check_interviewer_availability(
                interview_data['interviewer_id'],
                interview_data['scheduled_date'],
                interview_data['duration_minutes']
            )

            if not is_available:
                raise CustomError("Interviewer is not available at the specified time", 400)

            interview = Interview(
                id=str(uuid.uuid4()),
                job_id=interview_data['job_id'],
                candidate_id=interview_data['candidate_id'],
                interviewer_id=interview_data['interviewer_id'],
                interview_type=interview_data['interview_type'],
                scheduled_date=interview_data['scheduled_date'],
                duration_minutes=interview_data['duration_minutes'],
                location=interview_data.get('location'),
                meeting_link=interview_data.get('meeting_link'),
                notes=interview_data.get('notes')
            )

            saved_interview = self.__interview_repository.save_interview(interview)

            # Send notifications
            self.__send_interview_notifications(saved_interview)

            return InterviewDTO(many=False).dump(saved_interview)
        except Exception as e:
            raise CustomError(str(e), 400)

    def update_interview(self, interview_id, interview_data):
        try:
            interview = self.__interview_repository.get_interview_by_id(interview_id)
            if not interview:
                raise CustomError("Interview not found", 404)

            # Update only provided fields
            updatable_fields = {
                'scheduled_date', 'duration_minutes', 'location',
                'meeting_link', 'notes', 'feedback', 'score'
            }

            for field in interview_data:
                if field in updatable_fields:
                    setattr(interview, field, interview_data[field])

            interview.updated_at = datetime.utcnow()

            self.__interview_repository.update_interview(interview)
            return InterviewDTO(many=False).dump(interview)
        except Exception as e:
            raise CustomError(str(e), 400)

    def complete_interview(self, interview_id, feedback_data):
        try:
            interview = self.__interview_repository.get_interview_by_id(interview_id)
            if not interview:
                raise CustomError("Interview not found", 404)

            interview.status = InterviewStatus.COMPLETED
            interview.feedback = feedback_data.get('feedback')
            interview.score = feedback_data.get('score')
            interview.updated_at = datetime.utcnow()

            self.__interview_repository.update_interview(interview)
            return InterviewDTO(many=False).dump(interview)
        except Exception as e:
            raise CustomError(str(e), 400)

    # Todo: Create suitable email templates and proper enum
    # Todo: Make sure to pass a personalized email
    @staticmethod
    def __load_email_template(emailType, candidate):
        current_dir = os.path.dirname(__file__)
        template_dir = os.path.join(current_dir, '..', '..', 'helpers', 'email-templates')

        # Determine the template based on notification type
        template_map = {
            "CANCELLED": "interview_cancelled.html",
            "PENDING": "interview_pending.html",
        }

        template_file = template_map.get(emailType.value, "default_notification.html")  # Fallback template
        template_path = os.path.join(template_dir, template_file)

        with open(template_path, 'r') as file:
            html_template = file.read()

        # Replace placeholders in the template
        html_content = html_template.replace('{{name}}', f"{candidate.first_name} {candidate.last_name}")
        return html_content


    def cancel_interview(self, interview_id, reason, candidate):
        try:
            interview = self.__interview_repository.get_interview_by_id(interview_id)
            if not interview:
                raise CustomError("Interview not found", 404)

            interview.status = InterviewStatus.CANCELLED
            interview.cancelled_at = datetime.utcnow()
            interview.cancellation_reason = reason

            self.__interview_repository.update_interview(interview)

            # Send email cancellation notifications
            html_content = self.__load_email_template(EmailType.CANCELLED, candidate)
            self.__mailService.send_email(
                subject="Interview Cancelled",
                recipient=candidate.email,
                template_html=html_content
            )


            return InterviewDTO(many=False).dump(interview)
        except Exception as e:
            raise CustomError(str(e), 400)

    def __send_interview_notifications(self, interview, candidate):
        """Send notifications to both candidate and interviewer"""

        # Send email cancellation notifications
        html_content = self.__load_email_template(EmailType.PENDING, candidate)
        self.__mailService.send_email(
            subject="Interview Scheduled",
            recipient=candidate.email,
            template_html=html_content
        )