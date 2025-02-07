import os
import smtplib
import imaplib
import email
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional, Union

from src.config.ConfigBase import Config


class MailService:
    def __init__(self):
        """
        Initialize MailService with email configuration.

        Args:
            config: Dictionary containing email configuration:
                - username: Email username
                - password: Email password
                - smtp_host: SMTP server host
                - smtp_port: SMTP server port
                - imap_host: IMAP server host
                - imap_port: IMAP server port
        """

        self.config = Config()
        self.smtp_server = None
        self.imap_server = None
        self.attachments_dir = "email_attachments"

        # Create attachments directory if it doesn't exist
        if not os.path.exists(self.attachments_dir):
            os.makedirs(self.attachments_dir)

    def _connect_smtp(self) -> None:
        """Establish secure SMTP connection"""
        try:
            self.smtp_server = smtplib.SMTP_SSL(
                self.config.getConfig()["email"]["smtp_host"],
                self.config.getConfig()["email"]["smtp_port"]
            )
            self.smtp_server.login(
                self.config.getConfig()["email"]["username"],
                self.config.getConfig()["email"]["password"]
            )
        except Exception as e:
            print(f"SMTP connection error: {e}")
            raise

    def _connect_imap(self) -> None:
        """Establish secure IMAP connection"""
        try:
            self.imap_server = imaplib.IMAP4_SSL(
                self.config.getConfig()["email"]["imap_host"],
                self.config.getConfig()["email"]["imap_port"]
            )
            self.imap_server.login(
                self.config.getConfig()["email"]["username"],
                self.config.getConfig()["email"]["password"]
            )
        except Exception as e:
            print(f"IMAP connection error: {e}")
            raise

    def send_email(
            self,
            subject: str,
            recipient: str,
            body: str,
            is_html: bool = True,
    ) -> None:
        """
        Send email with optional attachments

        Args:
            subject: Email subject
            recipient: Recipient email address
            body: Email body content
            is_html: Whether the body content is HTML (default: True)
        """
        try:
            self._connect_smtp()

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.getConfig()["email"]["username"]
            msg['To'] = recipient

            # Attach body
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

            self.smtp_server.sendmail(
                self.config.getConfig()["email"]["username"],
                recipient,
                msg.as_string()
            )

            print(f"Email sent successfully to {recipient}")

        except Exception as e:
            print(f"Email sending failed: {e}")
            raise
        finally:
            if self.smtp_server:
                self.smtp_server.quit()

    def receive_emails(
            self,
            folder: str = "INBOX",
            unread_only: bool = True,
            mark_as_read: bool = True,
            max_emails: int = 10,
            search_criteria: str = None
    ) -> List[Dict]:
        """
        Receive emails with attachments from specified folder

        Args:
            folder: Email folder to check (default: "INBOX")
            unread_only: Whether to fetch only unread emails (default: True)
            mark_as_read: Whether to mark fetched emails as read (default: True)
            max_emails: Maximum number of emails to fetch (default: 10)
            search_criteria: Custom IMAP search criteria (default: None)

        Returns:
            List of dictionaries containing email details and local paths to downloaded attachments
        """
        try:
            self._connect_imap()

            # First, select the folder and check the response
            status, messages = self.imap_server.select(folder)
            if status != 'OK':
                raise Exception(f"Failed to select folder {folder}: {messages}")

            # Build search criteria
            if search_criteria:
                search_cmd = search_criteria
            else:
                search_cmd = '(UNSEEN)' if unread_only else 'ALL'

            # Now perform the search
            status, messages = self.imap_server.search(None, search_cmd)
            if status != 'OK':
                raise Exception(f"Search failed: {messages}")

            email_list = []

            # Process messages
            for message_num in messages[0].split()[-max_emails:]:
                email_data = self._process_email(message_num)
                if email_data:
                    email_list.append(email_data)

                    # Mark as read if requested
                    if mark_as_read:
                        self.imap_server.store(message_num, '+FLAGS', '\\Seen')

            return email_list

        except Exception as e:
            print(f"Email receiving failed: {e}")
            raise
        finally:
            if self.imap_server:
                self.imap_server.close()
                self.imap_server.logout()

    def _process_email(self, message_num: bytes) -> Dict:
        """
        Process a single email message and return its details

        Args:
            message_num: Message number in mailbox

        Returns:
            Dictionary containing email details and attachments
        """
        _, msg_data = self.imap_server.fetch(message_num, '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Get email details
        email_data = {
            "message_id": email_message["Message-ID"],
            "subject": self._decode_header(email_message["Subject"]),
            "from": self._decode_header(email_message["From"]),
            "to": self._decode_header(email_message["To"]),
            "date": email_message["Date"],
            "body_html": "",
            "body_text": "",
            "attachments": []
        }

        # Process body and attachments
        self._process_parts(email_message, email_data)

        return email_data

    def _process_parts(self, message: email.message.Message, email_data: Dict) -> None:
        """
        Process email parts to extract body and attachments

        Args:
            message: Email message object
            email_data: Dictionary to store email data
        """
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            # Get the content type and disposition
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition"))

            # Handle email body
            if disposition == "None" and content_type == "text/plain":
                email_data["body_text"] = part.get_payload(decode=True).decode()
            elif disposition == "None" and content_type == "text/html":
                email_data["body_html"] = part.get_payload(decode=True).decode()

            # Handle attachments
            elif disposition:
                try:
                    filename = part.get_filename()
                    if filename:
                        # Clean filename and add timestamp
                        clean_filename = self._clean_filename(filename)
                        filepath = os.path.join(self.attachments_dir, clean_filename)

                        # Save attachment
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))

                        email_data["attachments"].append({
                            "original_filename": filename,
                            "saved_filename": clean_filename,
                            "filepath": filepath,
                            "content_type": content_type
                        })
                except Exception as e:
                    print(f"Error processing attachment: {str(e)}")

    def _decode_header(self, header: Optional[str]) -> str:
        """
        Decode email header

        Args:
            header: Email header to decode

        Returns:
            Decoded header string
        """
        if not header:
            return ""
        decoded_header, encoding = decode_header(header)[0]
        if isinstance(decoded_header, bytes):
            return decoded_header.decode(encoding if encoding else 'utf-8')
        return decoded_header

    def _clean_filename(self, filename: str) -> str:
        """
        Clean filename and add timestamp to prevent overwrites

        Args:
            filename: Original filename

        Returns:
            Cleaned filename with timestamp
        """
        # Remove potentially unsafe characters
        clean_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        # Add timestamp
        name, ext = os.path.splitext(clean_name)
        return f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"


# Example usage
# if __name__ == "__main__":
#     # Email configuration
#     email_config = {
#         "username": "info.garret.events@gmail.com",
#         "password": "ekdp awmj tkgb shoo",
#         "smtp_host": "smtp.gmail.com",
#         "smtp_port": 465,
#         "imap_host": "imap.gmail.com",
#         "imap_port": 993
#     }
#
#     # Initialize mail service
#     mail_service = MailService()
#
#     # Receive emails
#     emails = mail_service.receive_emails(
#         unread_only=True,
#         mark_as_read=True,
#         max_emails=5
#     )
#
#     # Print email details
#     for email_data in emails:
#         print("\n" + "=" * 50)
#         print(f"From: {email_data['from']}")
#         print(f"To: {email_data['to']}")
#         print(f"Subject: {email_data['subject']}")
#         print(f"Date: {email_data['date']}")
#
#         # Print body (prefer HTML, fallback to text)
#         body = email_data['body_html'] or email_data['body_text']
#         print(f"\nBody:\n{body[:200]}...")  # Show first 200 chars
#
#         # Print attachment details
#         if email_data['attachments']:
#             print("\nAttachments:")
#             for attachment in email_data['attachments']:
#                 print(f"- {attachment['original_filename']} "
#                       f"(saved as: {attachment['saved_filename']})")