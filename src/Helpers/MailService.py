import os
import smtplib
import imaplib
import email
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from src.config.ConfigBase import Config


class MailService:
    def __init__(self):
        self.smtp_server = None
        self.imap_server = None
        self.config = Config()
        self.attachments_dir = "email_attachments"

        # Create attachments directory if it doesn't exist
        if not os.path.exists(self.attachments_dir):
            os.makedirs(self.attachments_dir)

    def _connect_smtp(self):
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

    def _connect_imap(self):
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

    def send_email(self, subject: str, recipient: str, template_html: str, attachments: Optional[List[str]] = None):
        """Send email with optional attachments"""
        try:
            self._connect_smtp()

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.getConfig()["email"]["from"]
            msg['To'] = recipient

            msg.attach(MIMEText(template_html, 'html'))

            if attachments:
                for filepath in attachments:
                    with open(filepath, 'rb') as file:
                        part = MIMEApplication(file.read(), Name=os.path.basename(filepath))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                        msg.attach(part)

            self.smtp_server.sendmail(
                self.config.getConfig()["email"]["from"],
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

    def receive_emails(self, folder: str = "INBOX", unread_only: bool = True, max_emails: int = 10) -> List[Dict]:
        """
        Receive emails with attachments from specified folder
        Returns list of dictionaries containing email details and local paths to downloaded attachments
        """
        try:
            self._connect_imap()
            self.imap_server.select(folder)

            # Search criteria
            search_criteria = '(UNSEEN)' if unread_only else 'ALL'
            _, messages = self.imap_server.search(None, search_criteria)

            email_list = []
            for message_num in messages[0].split()[:max_emails]:
                email_data = self._process_email(message_num)
                if email_data:
                    email_list.append(email_data)

            return email_list

        except Exception as e:
            print(f"Email receiving failed: {e}")
            raise
        finally:
            if self.imap_server:
                self.imap_server.close()
                self.imap_server.logout()

    def _process_email(self, message_num: bytes) -> Dict:
        """Process a single email message and return its details"""
        _, msg_data = self.imap_server.fetch(message_num, '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Process subject
        subject = self._decode_header(email_message["Subject"])

        # Process sender
        from_header = self._decode_header(email_message["From"])

        # Process date
        date = email_message["Date"]

        # Process attachments
        attachments = self._process_attachments(email_message)

        # Get email body
        body = self._get_email_body(email_message)

        return {
            "subject": subject,
            "from": from_header,
            "date": date,
            "body": body,
            "attachments": attachments
        }

    def _decode_header(self, header: Optional[str]) -> str:
        """Decode email header"""
        if not header:
            return ""
        decoded_header, encoding = decode_header(header)[0]
        if isinstance(decoded_header, bytes):
            return decoded_header.decode(encoding if encoding else 'utf-8')
        return decoded_header

    def _get_email_body(self, email_message) -> str:
        """Extract email body (prefer HTML, fallback to plain text)"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/html":
                    return part.get_payload(decode=True).decode()
                elif part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = email_message.get_payload(decode=True).decode()
        return body

    def _process_attachments(self, email_message) -> List[Dict[str, str]]:
        """Process and save attachments, return list of attachment details"""
        attachments = []

        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename:
                # Clean filename and add timestamp
                clean_filename = self._clean_filename(filename)
                filepath = os.path.join(self.attachments_dir, clean_filename)

                # Save attachment
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))

                attachments.append({
                    "original_filename": filename,
                    "saved_filename": clean_filename,
                    "filepath": filepath,
                    "content_type": part.get_content_type()
                })

        return attachments

    def _clean_filename(self, filename: str) -> str:
        """Clean filename and add timestamp to prevent overwrites"""
        # Remove potentially unsafe characters
        clean_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        # Add timestamp
        name, ext = os.path.splitext(clean_name)
        return f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

#
# # Example usage:
# if __name__ == "__main__":
#     mail = Mail()
#
#     # Receive emails
#     received_emails = mail.receive_emails(unread_only=True, max_emails=5)
#
#     # Process received emails
#     for email_data in received_emails:
#         print(f"\nSubject: {email_data['subject']}")
#         print(f"From: {email_data['from']}")
#         print(f"Date: {email_data['date']}")
#         print(f"Number of attachments: {len(email_data['attachments'])}")
#
#         # Print attachment details
#         for attachment in email_data['attachments']:
#             print(f"\nAttachment: {attachment['original_filename']}")
#             print(f"Saved as: {attachment['filepath']}")
#             print(f"Type: {attachment['content_type']}")

