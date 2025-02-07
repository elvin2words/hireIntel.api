import os
from datetime import datetime
import uuid
from enum import Enum
from typing import Dict, List
from src.Helpers.ErrorHandling import CustomError
from src.Helpers.MailService import MailService
from src.Modules.Interviews.InterviewDTOs import EmailNotificationDTO
from src.Modules.Interviews.InterviewModels import EmailNotification

from src.Modules.Interviews.InterviewRepository import EmailNotificationRepository


class NotificationType(Enum):
    ACCEPTANCE = 'ACCEPTANCE'
    REJECTION = 'REJECTION'


class InterviewNotificationService:
    def __init__(self):
        self.__email_repo = EmailNotificationRepository()
        self.__mail = MailService()
        self.template_dir = self._get_template_dir()

    @staticmethod
    def _get_template_dir() -> str:
        """
        Get the absolute path to the email templates directory.
        Templates are located in src/Static/EmailTemplates/
        """
        # Get the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Navigate to src directory (two levels up from current file)
        src_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))

        # Path to templates directory
        template_dir = os.path.join(src_dir, 'Static', 'EmailTemplates')

        if not os.path.exists(template_dir):
            raise CustomError(f"Email templates directory not found at: {template_dir}", 500)

        return template_dir

    @staticmethod
    def __format_content_paragraphs(content: str) -> List[str]:
        """
        Format email content into paragraphs based on sentences.
        """
        try:
            if not content:
                return []

            # Split content into sentences and clean them
            sentences = []
            for sentence in content.split('.'):
                cleaned = sentence.strip()
                if cleaned:
                    # Don't add period if sentence ends with special characters
                    if not cleaned[-1] in ['!', '?']:
                        cleaned += '.'
                    sentences.append(cleaned)

            # Group sentences into paragraphs
            paragraphs = []
            current_paragraph = []

            for sentence in sentences:
                current_paragraph.append(sentence)

                # Start new paragraph based on conditions
                if (len(current_paragraph) >= 2 or
                        any(keyword in sentence.lower() for keyword in
                            ['interview', 'experience', 'skills', 'available', 'thank', 'regards', 'best'])):
                    paragraph = ' '.join(current_paragraph).strip()
                    if paragraph:
                        paragraphs.append(paragraph)
                    current_paragraph = []

            # Add any remaining sentences
            if current_paragraph:
                paragraph = ' '.join(current_paragraph).strip()
                if paragraph:
                    paragraphs.append(paragraph)

            return paragraphs

        except Exception as e:
            raise CustomError(f"Failed to format paragraphs: {str(e)}", 400)

    def __load_email_template(self, notification_type, notification_data):
        """
        Load and populate email template with notification data.
        """
        try:
            # Validate required data
            if not notification_type:
                raise CustomError("Notification type is required", 400)
            if not notification_data:
                raise CustomError("Notification data is required", 400)

            # Get template file
            template_map = {
                "ACCEPTANCE": "acceptance.html",
                "REJECTION": "rejection.html",
            }

            template_file = template_map.get(notification_type.value)
            if not template_file:
                raise CustomError(f"Invalid notification type: {notification_type.value}", 400)

            template_path = os.path.join(self.template_dir, template_file)

            # Read template file
            try:
                with open(template_path, 'r', encoding='utf-8') as file:
                    html_template = file.read()
            except Exception as e:
                raise CustomError(f"Failed to read template file: {str(e)}", 500)

            # Format content into paragraphs
            email_content = notification_data.get('email_content', '')
            paragraphs = self.__format_content_paragraphs(email_content) if email_content else []

            # Convert paragraphs to HTML format
            formatted_content = '\n'.join([f'<p class="content-paragraph">{p}</p>' for p in paragraphs])

            # Create base replacements that are common to both types
            replacements = {
                '{{personalization.candidate_name}}': str(notification_data.get('candidate_name', '')),
                '{{content}}': formatted_content,
            }

            # Add type-specific replacements
            if notification_type == NotificationType.ACCEPTANCE:
                interview_details = notification_data.get('interview_details', {})
                replacements.update({
                    '{{personalization.custom_fields.interview_date}}': str(interview_details.get('date', '')),
                    '{{personalization.custom_fields.interview_time}}': str(interview_details.get('time', '')),
                    '{{personalization.custom_fields.interview_location}}': str(interview_details.get('location', ''))
                })
            elif notification_type == NotificationType.REJECTION:
                feedback = notification_data.get('feedback', {})
                replacements.update({
                    '{{feedback.improvement_areas}}': str(feedback.get('improvement_areas', '')),
                    '{{feedback.missing_skills}}': str(feedback.get('missing_skills', '')),
                    '{{feedback.experience_feedback}}': str(feedback.get('experience_feedback', ''))
                })

            # Apply all replacements to the template
            html_content = html_template
            for placeholder, value in replacements.items():
                if value is not None:  # Extra check before replacement
                    # Don't escape HTML for content that contains paragraph tags
                    if placeholder == '{{content}}':
                        html_content = html_content.replace(placeholder, value)
                    else:
                        html_content = html_content.replace(placeholder, self.__sanitize_html(value))

            return html_content

        except Exception as e:
            raise CustomError(f"Failed to process email template: {str(e)}", 400)

    def create_notification(self, candidate: dict, notification_data: Dict,
                            notification_type: NotificationType) -> Dict:
        """
        Create and send a notification to a candidate with improved error handling.
        """
        try:
            # Validate inputs
            if not candidate:
                raise CustomError("Candidate data is required", 400)
            if not notification_data:
                raise CustomError("Notification data is required", 400)
            if not notification_type:
                raise CustomError("Notification type is required", 400)

            # Ensure required candidate fields exist
            candidate_id = candidate.get('id')
            candidate_email = candidate.get('email')
            if not candidate_id or not candidate_email:
                raise CustomError("Candidate must have id and email", 400)

            # Create notification record
            notification = EmailNotification(
                id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                subject=notification_data.get("subject", "Interview Update"),
                content=notification_data.get("email_content", ""),
                email_type=notification_type,
                sent_at=datetime.utcnow(),
                status="PENDING"
            )

            # Generate email content from template
            try:
                html_content = self.__load_email_template(
                    notification_type,
                    notification_data
                )
                if not html_content:
                    raise CustomError("Failed to generate email content", 400)
            except Exception as e:
                raise CustomError(f"Template generation failed: {str(e)}", 400)

            # Send email
            try:
                self.__mail.send_email(
                    subject=notification.subject,
                    recipient=candidate_email,
                    body=html_content,
                )
            except Exception as e:
                raise CustomError(f"Failed to send email: {str(e)}", 400)

            notification.status = "SENT"
            return EmailNotificationDTO(many=False).dump(notification)

        except Exception as e:
            raise CustomError(f"Failed to create/send notification: {str(e)}", 400)

    @staticmethod
    def __sanitize_html(text: str) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.

        Args:
            text (str): Raw HTML content

        Returns:
            str: Sanitized HTML content
        """
        import html
        return html.escape(text, quote=True)


    # def create_notification(self,
    #                         candidate: dict,
    #                         notification_data: Dict,
    #                         notification_type: NotificationType) -> Dict:
    #     """
    #     Create and send a notification to a candidate
    #
    #     Args:
    #         candidate: Unique identifier for the candidate
    #         notification_data: Dict containing notification content
    #         notification_type: Type of notification (acceptance/rejection/etc)
    #     """
    #     try:
    #         # print("Creating notification...........")
    #         # Create notification record
    #         notification = EmailNotification(
    #             id=str(uuid.uuid4()),
    #             candidate_id=candidate['id'],
    #             subject=notification_data["subject"],
    #             content=notification_data["email_content"],
    #             email_type=notification_type,
    #             sent_at=datetime.utcnow(),
    #             status="PENDING"
    #         )
    #
    #         # print("Notification is : ", notification)
    #
    #         # Generate email content from template
    #         html_content = self.__load_email_template(
    #             notification_type,
    #             notification_data
    #         )
    #
    #         # print("fetched html content......")
    #         # print("Attempting to send notification to : ", candidate)
    #         # Send email
    #
    #         self.__mail.send_email(
    #                 subject=notification.subject,
    #                 recipient=candidate["email"],
    #                 body=html_content,
    #         )
    #         print("Notification sent successfully...")
    #         notification.status = "SENT"
    #
    #         return EmailNotificationDTO(many=False).dump(notification)
    #
    #     except Exception as e:
    #         raise CustomError(f"Failed to create/send notification: {str(e)}", 400)
