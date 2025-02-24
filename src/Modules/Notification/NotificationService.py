import os
from datetime import datetime
import uuid
import logging
from enum import Enum
from typing import Dict, List, Union
from src.Helpers.ErrorHandling import CustomError
from src.Helpers.MailService import MailService

from src.Modules.Notification.NotificationDTOs import EmailNotificationDTO
from src.Modules.Notification.NotificationModels import EmailNotification
from src.Modules.Notification.NotificationRepository import EmailNotificationRepository



"""
This NotificationService focuses on managing notifications, primarily by sending emails. 
It loads email templates, processes them based on the type of notification, and uses a MailService to send the final email.

"""

class NotificationType(Enum):
    RESUME_NOT_FOUND = 'RESUME_NOT_FOUND'
    ACCEPTANCE = 'ACCEPTANCE'
    REJECTION = 'REJECTION'
    MISSING_FIELDS = 'MISSING_FIELDS'
    JOB_NOT_FOUND ='JOB_NOT_FOUND'
    APPLICATION_RECEIVED = 'APPLICATION_RECEIVED'
    INTERVIEW_SCHEDULED = 'INTERVIEW_SCHEDULED'


class NotificationService:
    _template_cache = {}
    
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


    # def __load_email_template(self, notification_type, notification_data):
    #     """
    #     Load and populate email template with notification data.
    #     """
    #     try:
    #         # Validate required data
    #         if not notification_type:
    #             raise CustomError("Notification type is required", 400)
    #
    #         # Get template file
    #         template_map = {
    #             "ACCEPTANCE": "acceptance.html",
    #             "REJECTION": "rejection.html",
    #             "MISSING_FIELDS": "missing_fields.html",
    #             "JOB_NOT_FOUND": "job_not_found.html",
    #             "RESUME_NOT_FOUND": "resume_not_found.html"
    #         }
    #
    #         # Get the template value based on either Enum value or string
    #         template_key = notification_type.value if hasattr(notification_type, 'value') else notification_type
    #         template_file = template_map.get(template_key)
    #
    #         if not template_file:
    #             raise CustomError(f"Invalid notification type: {template_key}", 400)
    #
    #         template_path = os.path.join(self.template_dir, template_file)
    #
    #         # Read template file
    #         try:
    #             with open(template_path, 'r', encoding='utf-8') as file:
    #                 html_template = file.read()
    #         except Exception as e:
    #             raise CustomError(f"Failed to read template file: {str(e)}", 500)
    #
    #         # For RESUME_NOT_FOUND, we don't need any replacements
    #         if template_key == "RESUME_NOT_FOUND":
    #             return html_template
    #
    #         # For other templates, we need notification_data
    #         if not notification_data:
    #             raise CustomError("Notification data is required", 400)
    #
    #         # Handle different template types
    #         if template_key in ["ACCEPTANCE", "REJECTION"]:
    #             # Format content into paragraphs for acceptance/rejection
    #             email_content = notification_data.get('email_content', '')
    #             paragraphs = self.__format_content_paragraphs(email_content) if email_content else []
    #             formatted_content = '\n'.join([f'<p class="content-paragraph">{p}</p>' for p in paragraphs])
    #
    #             # Create base replacements
    #             replacements = {
    #                 '{{personalization.candidate_name}}': str(notification_data.get('candidate_name', '')),
    #                 '{{content}}': formatted_content,
    #             }
    #
    #             # Add type-specific replacements
    #             if template_key == "ACCEPTANCE":
    #                 interview_details = notification_data.get('interview_details', {})
    #                 replacements.update({
    #                     '{{personalization.custom_fields.interview_date}}': str(interview_details.get('date', '')),
    #                     '{{personalization.custom_fields.interview_time}}': str(interview_details.get('time', '')),
    #                     '{{personalization.custom_fields.interview_location}}': str(
    #                         interview_details.get('location', ''))
    #                 })
    #             elif template_key == "REJECTION":
    #                 feedback = notification_data.get('feedback', {})
    #                 replacements.update({
    #                     '{{feedback.improvement_areas}}': str(feedback.get('improvement_areas', '')),
    #                     '{{feedback.missing_skills}}': str(feedback.get('missing_skills', '')),
    #                     '{{feedback.experience_feedback}}': str(feedback.get('experience_feedback', ''))
    #                 })
    #         else:
    #             # Handle application feedback templates
    #             replacements = {}
    #             if template_key == "MISSING_FIELDS":
    #                 missing_fields = notification_data.get('missing_fields', [])
    #                 list_items = [f"<li>{self.__sanitize_html(item)}</li>" for item in missing_fields]
    #                 formatted_list = "<ul>" + "".join(list_items) + "</ul>"
    #                 replacements = {
    #                     '{{missing_fields}}': formatted_list,
    #                     '{{fields_count}}': str(len(missing_fields))
    #                 }
    #             elif template_key == "JOB_NOT_FOUND":
    #                 replacements = {
    #                     '{{error_message}}': str(notification_data.get('error_message', ''))
    #                 }
    #
    #         # Apply all replacements to the template
    #         html_content = html_template
    #         for placeholder, value in replacements.items():
    #             if value is not None:
    #                 if '<' in value and '>' in value:  # Contains HTML
    #                     html_content = html_content.replace(placeholder, value)
    #                 else:
    #                     html_content = html_content.replace(placeholder, self.__sanitize_html(value))
    #
    #         return html_content
    #
    #     except Exception as e:
    #         raise CustomError(f"Failed to process email template: {str(e)}", 400)

    def __load_email_template(self, notification_type, notification_data):
        """
        Load and populate email template with notification data.
        """
        try:
            # Validate required data
            if not notification_type:
                raise CustomError("Notification type is required", 400)

            # Get template file
            template_map = {
                "ACCEPTANCE": "acceptance.html",
                "REJECTION": "rejection.html",
                "MISSING_FIELDS": "missing_fields.html",
                "JOB_NOT_FOUND": "job_not_found.html",
                "RESUME_NOT_FOUND": "resume_not_found.html",
                "APPLICATION_RECEIVED": "application_received.html"
            }

            # Get the template value based on either Enum value or string
            template_key = notification_type.value if hasattr(notification_type, 'value') else notification_type
            template_file = template_map.get(template_key)

            if not template_file:
                raise CustomError(f"Invalid notification type: {template_key}", 400)

            template_path = os.path.join(self.template_dir, template_file)

            # Read template file
            try:
                with open(template_path, 'r', encoding='utf-8') as file:
                    html_template = file.read()
            except Exception as e:
                raise CustomError(f"Failed to read template file: {str(e)}", 500)

            # For templates that don't need replacements
            if template_key in ["RESUME_NOT_FOUND", "APPLICATION_RECEIVED"]:
                return html_template

            # For other templates, we need notification_data
            if not notification_data:
                raise CustomError("Notification data is required", 400)

            # Handle different template types
            if template_key in ["ACCEPTANCE", "REJECTION"]:
                # Format content into paragraphs for acceptance/rejection
                email_content = notification_data.get('email_content', '')
                paragraphs = self.__format_content_paragraphs(email_content) if email_content else []
                formatted_content = '\n'.join([f'<p class="content-paragraph">{p}</p>' for p in paragraphs])

                # Create base replacements
                replacements = {
                    '{{personalization.candidate_name}}': str(notification_data.get('candidate_name', '')),
                    '{{content}}': formatted_content,
                }

                # Add type-specific replacements
                if template_key == "ACCEPTANCE":
                    interview_details = notification_data.get('interview_details', {})
                    replacements.update({
                        '{{personalization.custom_fields.interview_date}}': str(interview_details.get('date', '')),
                        '{{personalization.custom_fields.interview_time}}': str(interview_details.get('time', '')),
                        '{{personalization.custom_fields.interview_location}}': str(
                            interview_details.get('location', ''))
                    })
                elif template_key == "REJECTION":
                    feedback = notification_data.get('feedback', {})
                    replacements.update({
                        '{{feedback.improvement_areas}}': str(feedback.get('improvement_areas', '')),
                        '{{feedback.missing_skills}}': str(feedback.get('missing_skills', '')),
                        '{{feedback.experience_feedback}}': str(feedback.get('experience_feedback', ''))
                    })
            else:
                # Handle application feedback templates
                replacements = {}
                if template_key == "MISSING_FIELDS":
                    missing_fields = notification_data.get('missing_fields', [])
                    list_items = [f"<li>{self.__sanitize_html(item)}</li>" for item in missing_fields]
                    formatted_list = "<ul>" + "".join(list_items) + "</ul>"
                    replacements = {
                        '{{missing_fields}}': formatted_list,
                        '{{fields_count}}': str(len(missing_fields))
                    }
                elif template_key == "JOB_NOT_FOUND":
                    replacements = {
                        '{{error_message}}': str(notification_data.get('error_message', ''))
                    }

            # Apply all replacements to the template
            html_content = html_template
            for placeholder, value in replacements.items():
                if value is not None:
                    if '<' in value and '>' in value:  # Contains HTML
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

    def sendJobApplicationNotificationFeedback(self, data: Union[List[str], str], recipient_email: str,
                                               notification_type: NotificationType) -> Dict:
        """
        Send feedback notification for job application issues.
        """
        try:
            # Validate inputs
            if not recipient_email:
                raise CustomError("Recipient email is required", 400)
            if not notification_type:
                raise CustomError("Notification type is required", 400)

            # Only validate data for types that require it
            if notification_type not in [NotificationType.RESUME_NOT_FOUND,
                                         NotificationType.APPLICATION_RECEIVED] and data is None:
                raise CustomError("Feedback data is required", 400)

            # Process data based on notification type
            template_data = {}

            if notification_type == NotificationType.MISSING_FIELDS:
                if not isinstance(data, list):
                    raise CustomError("Missing fields data must be a list", 400)

                subject = "Job Application: Missing Required Information"
                missing_fields_list = [field.replace('_', ' ').title() for field in data]
                content = "Missing fields: " + ", ".join(missing_fields_list)
                template_data = {
                    'missing_fields': missing_fields_list,
                    'fields_count': len(missing_fields_list)
                }

            elif notification_type == NotificationType.JOB_NOT_FOUND:
                if not isinstance(data, str):
                    raise CustomError("Job not found data must be a string", 400)

                subject = "Job Application: Invalid Job Reference"
                content = data
                template_data = {
                    'error_message': data
                }

            elif notification_type == NotificationType.RESUME_NOT_FOUND:
                subject = "Job Application: Resume Required"
                content = "Resume not found in application"
                # No template data needed for resume not found

            elif notification_type == NotificationType.APPLICATION_RECEIVED:
                subject = "Job Application: Application Received"
                content = "Application successfully received and being processed"
                # No template data needed for application received

            else:
                raise CustomError(f"Invalid notification type: {notification_type.value}", 400)

            # Create notification record
            notification = EmailNotification(
                id=str(uuid.uuid4()),
                candidate_id=None,  # No candidate ID as this is application feedback
                subject=subject,
                content=content,
                email_type=notification_type.value,
                sent_at=datetime.utcnow(),
                status="PENDING"
            )

            # Generate email content from template
            try:
                html_content = self.__load_email_template(
                    notification_type,
                    template_data
                )
                if not html_content:
                    raise CustomError("Failed to generate email content", 400)
            except Exception as e:
                raise CustomError(f"Template generation failed: {str(e)}", 400)

            # Send email
            try:
                self.__mail.send_email(
                    subject=notification.subject,
                    recipient=recipient_email,
                    body=html_content,
                )
            except Exception as e:
                raise CustomError(f"Failed to send email: {str(e)}", 400)

            notification.status = "SENT"
            return EmailNotificationDTO(many=False).dump(notification)

        except Exception as e:
            raise CustomError(f"Failed to send application feedback notification: {str(e)}", 400)

    # def sendJobApplicationNotificationFeedback(self, data: Union[List[str], str], recipient_email: str,
    #                                            notification_type: NotificationType) -> Dict:
    #     """
    #     Send feedback notification for job application issues.
    #     """
    #     try:
    #         # Validate inputs
    #         if not recipient_email:
    #             raise CustomError("Recipient email is required", 400)
    #         if not notification_type:
    #             raise CustomError("Notification type is required", 400)
    #
    #         # Only validate data for non-RESUME_NOT_FOUND types
    #         if notification_type != NotificationType.RESUME_NOT_FOUND and data is None:
    #             raise CustomError("Feedback data is required", 400)
    #
    #         # Process data based on notification type
    #         template_data = {}
    #
    #         if notification_type == NotificationType.MISSING_FIELDS:
    #             if not isinstance(data, list):
    #                 raise CustomError("Missing fields data must be a list", 400)
    #
    #             subject = "Job Application: Missing Required Information"
    #             missing_fields_list = [field.replace('_', ' ').title() for field in data]
    #             content = "Missing fields: " + ", ".join(missing_fields_list)
    #             template_data = {
    #                 'missing_fields': missing_fields_list,
    #                 'fields_count': len(missing_fields_list)
    #             }
    #
    #         elif notification_type == NotificationType.JOB_NOT_FOUND:
    #             if not isinstance(data, str):
    #                 raise CustomError("Job not found data must be a string", 400)
    #
    #             subject = "Job Application: Invalid Job Reference"
    #             content = data
    #             template_data = {
    #                 'error_message': data
    #             }
    #
    #         elif notification_type == NotificationType.RESUME_NOT_FOUND:
    #             subject = "Job Application: Resume Required"
    #             content = "Resume not found in application"
    #             # No template data needed for resume not found
    #
    #         else:
    #             raise CustomError(f"Invalid notification type: {notification_type.value}", 400)
    #
    #         # Create notification record
    #         notification = EmailNotification(
    #             id=str(uuid.uuid4()),
    #             candidate_id=None,  # No candidate ID as this is application feedback
    #             subject=subject,
    #             content=content,
    #             email_type=notification_type.value,
    #             sent_at=datetime.utcnow(),
    #             status="PENDING"
    #         )
    #
    #         # Generate email content from template
    #         try:
    #             html_content = self.__load_email_template(
    #                 notification_type,
    #                 template_data
    #             )
    #             if not html_content:
    #                 raise CustomError("Failed to generate email content", 400)
    #         except Exception as e:
    #             raise CustomError(f"Template generation failed: {str(e)}", 400)
    #
    #         # Send email
    #         try:
    #             self.__mail.send_email(
    #                 subject=notification.subject,
    #                 recipient=recipient_email,
    #                 body=html_content,
    #             )
    #         except Exception as e:
    #             raise CustomError(f"Failed to send email: {str(e)}", 400)
    #
    #         notification.status = "SENT"
    #         return EmailNotificationDTO(many=False).dump(notification)
    #
    #     except Exception as e:
    #         raise CustomError(f"Failed to send application feedback notification: {str(e)}", 400)