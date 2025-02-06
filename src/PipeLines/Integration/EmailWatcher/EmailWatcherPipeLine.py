import os
from flask import Flask
from datetime import datetime
from typing import Dict, List, Any, Union
import email.utils

from src.Helpers.MailService import MailService
from src.Helpers.ErrorHandling import CustomError
from src.PipeLines.Integration.EmailWatcher.EmailProccessor import EmailProcessor
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor


class EmailMonitorConfig(PipelineConfig):
    def __init__(self,
                 name: str = "email_monitor",
                 batch_size: int = 10,
                 process_interval: int = 300,
                 start_date: str = None,
                 end_date: str = None,
                 email_folder: str = "INBOX",
                 attachment_types: List[str] = None):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        self.email_folder = email_folder
        self.attachment_types = attachment_types or ['.pdf', '.doc', '.docx']


class EmailMonitorPipeline(BasePipeline):
    def __init__(self, app: Flask, config: EmailMonitorConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: EmailMonitorConfig = config
        self.mail_service = MailService()
        self._last_processed_date = None
        self.__email_processor = EmailProcessor()

    def _parse_email_date(self, date_str: str) -> datetime:
        try:
            time_tuple = email.utils.parsedate_tz(date_str)
            return datetime(*time_tuple[:6]) if time_tuple else datetime.now()
        except Exception as e:
            self.logger.error(f"Error parsing date {date_str}: {str(e)}")
            return datetime.now()

    def _is_email_in_date_range(self, email_date: str) -> bool:
        email_dt = self._parse_email_date(email_date)
        if self.config.start_date and email_dt < self.config.start_date:
            return False
        if self.config.end_date and email_dt > self.config.end_date:
            return False
        return True

    def get_input_data(self) -> List[Dict]:
        """Retrieve unread emails from configured folder"""
        if self.config.end_date and datetime.now() > self.config.end_date:
            return []

        return self.mail_service.receive_emails(
            folder=self.config.email_folder,
            unread_only=True,
            mark_as_read=True,
            max_emails=self.config.batch_size
        )

    def process_item(self, _email: Dict) -> Union[Dict, None]:
        """Process a single email"""
        if not self._is_email_in_date_range(_email['date']):
            return None

        valid_attachments = [
            attachment for attachment in _email['attachments']
            if os.path.splitext(attachment['original_filename'])[1].lower()
               in self.config.attachment_types
        ]

        if not valid_attachments:
            return None

        _email['valid_attachments'] = valid_attachments
        success, message = self.__email_processor.process_email(_email)

        if not success:
            raise CustomError(f"Failed to process email: {message}", 400)

        return _email

    def update_output(self, processed_emails: List[Dict]) -> None:
        """Update output after processing emails"""
        try:
            self.__email_processor.cleanup_attachments('email_attachments')
            self.logger.info(f"Successfully processed {len(processed_emails)} emails")
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}")
            raise

    def handle_item_failure(self, _email: Dict, error: Exception) -> None:
        """Handle individual email processing failures"""
        self.logger.error(f"Failed to process email from {_email.get('from', 'unknown')}: {str(error)}")


# import os
#
# from flask import Flask
# from datetime import datetime
# from typing import Dict, List
# import email.utils
#
# from src.Helpers.MailService import MailService
# from src.Helpers.ErrorHandling import CustomError
# from src.PipeLines.Integration.EmailWatcher.EmailProccessor import EmailProcessor
# from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
# from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
# from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
#
#
# class EmailMonitorConfig(PipelineConfig):
#     def __init__(self,
#                  name: str = "email_monitor",
#                  batch_size: int = 10,
#                  process_interval: int = 300,
#                  start_date: str = None,
#                  end_date: str = None,
#                  email_folder: str = "INBOX",
#                  attachment_types: List[str] = None):
#         super().__init__(name, batch_size, process_interval=process_interval)
#         # Convert date strings to datetime objects
#         self.start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
#         self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
#         self.email_folder = email_folder
#         self.attachment_types = attachment_types or ['.pdf', '.doc', '.docx']
#
#
# class EmailMonitorPipeline(BasePipeline):
#     def __init__(self, app: Flask, config: EmailMonitorConfig, monitor: PipelineMonitor):
#         super().__init__(app, config, monitor)
#         self.config: EmailMonitorConfig = config
#         self.mail_service = MailService()
#         self._last_processed_date = None
#         self.__email_processor = EmailProcessor()
#
#     def _parse_email_date(self, date_str: str) -> datetime:
#         """Convert email date string to datetime object"""
#         try:
#             # Parse the email date format
#             time_tuple = email.utils.parsedate_tz(date_str)
#             if time_tuple:
#                 dt = datetime(*time_tuple[:6])
#                 return dt
#             return datetime.now()  # Fallback
#         except Exception as e:
#             self.logger.error(f"Error parsing date {date_str}: {str(e)}")
#             return datetime.now()  # Fallback
#
#     def _is_email_in_date_range(self, email_date: str) -> bool:
#         """Check if email falls within the configured date range"""
#         email_dt = self._parse_email_date(email_date)
#
#         if self.config.start_date and email_dt < self.config.start_date:
#             return False
#         if self.config.end_date and email_dt > self.config.end_date:
#             return False
#         return True
#
#
#     def _process_email_batch(self) -> List[Dict]:
#         """Process a batch of emails within the date range"""
#         processed_emails = []
#
#         try:
#             # Get emails from the mail service
#             emails = self.mail_service.receive_emails(
#                 folder=self.config.email_folder,
#                 unread_only=True,
#                 mark_as_read=True,
#                 max_emails=self.config.batch_size
#             )
#
#             # Process each email
#             for _email in emails:
#                 self.logger.info(f"Processing email from: {_email['from']}")
#                 print(f"Processing email from: {_email['from']}")
#
#                 # Check if email is within date range
#                 if not self._is_email_in_date_range(_email['date']):
#                     self.logger.info("Email outside date range, skipping")
#                     continue
#
#                 # Check for attachments with allowed types
#                 valid_attachments = []
#                 for attachment in _email['attachments']:
#                     file_ext = os.path.splitext(attachment['original_filename'])[1].lower()
#                     if file_ext in self.config.attachment_types:
#                         valid_attachments.append(attachment)
#
#                 if not valid_attachments:
#                     self.logger.info("No valid attachments found, skipping")
#                     continue
#
#                 # Add valid attachments to email
#                 _email['valid_attachments'] = valid_attachments
#
#                 try:
#                     # Process email and create XML
#                     success, message = self.__email_processor.process_email(_email)
#
#                     if success:
#                         processed_emails.append(_email)
#                         self.logger.info(f"Successfully processed email: {message}")
#                     else:
#                         self.logger.error(f"Failed to process email: {message}")
#
#                 except Exception as e:
#                     self.logger.error(f"Error processing individual email: {str(e)}")
#                     continue
#
#             # Cleanup attachments directory after processing all emails
#             try:
#                 self.__email_processor.cleanup_attachments('email_attachments')
#             except Exception as e:
#                 self.logger.error(f"Error cleaning up attachments: {str(e)}")
#
#             return processed_emails
#
#         except Exception as e:
#             self.logger.error(f"Error processing email batch: {str(e)}")
#             raise CustomError(f"Email batch processing failed: {str(e)}", 400)
#
#     def process_batch(self):
#         """Main pipeline batch processing method"""
#         try:
#             self.logger.info("Starting email monitoring batch process")
#             self.monitor.update_state(
#                 self.config.name,
#                 PipelineStatus.RUNNING,
#                 "Processing new emails"
#             )
#
#             # Check if we're still within the monitoring period
#             current_time = datetime.now()
#             if self.config.end_date and current_time > self.config.end_date:
#                 self.logger.info("Monitoring period has ended")
#                 self.monitor.update_state(
#                     self.config.name,
#                     PipelineStatus.STOPPED,
#                     "Monitoring period completed"
#                 )
#                 return
#
#             # Process emails
#             processed_emails = self._process_email_batch()
#
#             if processed_emails:
#                 self.logger.info(f"Processed {len(processed_emails)} new emails")
#                 # Here you can add custom logic to handle the processed emails
#                 # For example, store them in a database, trigger notifications, etc.
#
#                 self.monitor.update_state(
#                     self.config.name,
#                     PipelineStatus.IDLE,
#                     f"Successfully processed {len(processed_emails)} emails"
#                 )
#             else:
#                 self.logger.info("No new emails to process")
#                 self.monitor.update_state(
#                     self.config.name,
#                     PipelineStatus.IDLE,
#                     "No new emails found"
#                 )
#
#         except Exception as e:
#             self.logger.error(f"Email monitoring failed: {str(e)}")
#             self.monitor.update_state(
#                 self.config.name,
#                 PipelineStatus.ERROR,
#                 "Email monitoring error",
#                 error_message=str(e)
#             )
#             raise