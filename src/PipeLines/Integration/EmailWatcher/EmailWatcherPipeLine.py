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

        success, message = self.__email_processor.process_email(_email, self.config.attachment_types)

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