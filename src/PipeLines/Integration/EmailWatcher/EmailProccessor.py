import json
import logging
import os
import uuid
import shutil
import xml.etree.ElementTree as ET
from typing import Tuple, Optional, Union
from xml.dom import minidom
from datetime import datetime
import re

from src.Helpers.LLMService import LLMService
from src.Modules.Candidate.Documents.DocumentModels import DocumentInfo, CandidateDocument, PersonInfo
from src.Modules.Jobs.JobService import JobService
from src.Modules.Notification.NotificationService import NotificationService, NotificationType


class EmailProcessor:
    def __init__(self, watcher_folder="./src/PipeLines/Integration/FileWatcher/Watcher/watcher_folder"):
        self.watcher_folder = watcher_folder
        self.__llmService = LLMService()
        self.__notificationService = NotificationService()
        self.__jobService = JobService()
        # Create watcher folder if it doesn't exist
        os.makedirs(self.watcher_folder, exist_ok=True)

    def format_email_for_llm(self, email_data: dict) -> str:
        """
        Creates a structured prompt for LLM to analyze job application emails with labeled candidate information.

        Args:
            email_data (dict): Email data containing from, to, subject, and body fields
        Returns:
            str: Formatted prompt for LLM
        """
        email_content = f"""
                            From: {email_data.get('from', 'N/A')}
                            To: {email_data.get('to', 'N/A')}
                            Subject: {email_data.get('subject', 'N/A')}
                        
                            Body:
                            {email_data.get('body_text', 'N/A')}
                        """

        prompt = f"""
                    Analyze the following job application email to extract candidate information. The email body contains labeled candidate details in a structured format.

                    Email Content:
                    {email_content}

                    Task:
                    Extract the following fields from the email body where they are explicitly labeled:
                    - first name
                    - middle name
                    - last name
                    - job id

                    Important Notes:
                    1. The information appears after labels like "first name:", "middle name:", "last name:", "job id:"
                    2. Labels might be in different cases (upper/lower) or have varying spacing
                    3. Some fields might be missing or empty
                    4. The job id should be extracted exactly as presented

                    Common Opening Variations:
                    The email may start with various phrases such as:
                    - "Applying for a role in [position]"
                    - "I am applying for the [position] position"
                    - "I would like to apply for [position]"
                    - "This is an application for the [position]"
                    - "I am interested in the [position] role"

                    After the opening, there will be labeled candidate information in this format:
                    first name  :  [value]
                    Middle name:  [value]
                    last name : [value]
                    Job id: [value]

                    The opening statement and exact spacing may vary, but the labeled information will always be present.

                    Response Format:
                    {{
                        "is_job_application": boolean,
                        "has_missing_fields": boolean,
                        "missing_fields": ["field1", "field2"],
                        "extracted_info": {{
                            "first_name": string | null,
                            "middle_name": string | null,
                            "last_name": string | null,
                            "job_id": string | null
                        }}
                    }}

                    Rules for Extraction:
                    1. Extract values exactly as they appear after the labels
                    2. Trim any extra whitespace from the values
                    3. If a field is not found, set it to null
                    4. Consider the email a job application if it:
                       - Contains any variation of a job application opening statement
                       - Has at least one of the labeled fields (first name, last name, etc.)
                    5. Add any missing required field to the missing_fields array
                    6. Ignore variations in the opening statement - focus on extracting the labeled information
                    7. The opening statement's exact wording doesn't matter as long as it indicates a job application

                    Example Response:
                    {{
                        "is_job_application": true,
                        "has_missing_fields": false,
                        "missing_fields": [],
                        "extracted_info": {{
                            "first_name": "Kudzai",
                            "middle_name": "Prichard",
                            "last_name": "Matizirofa",
                            "job_id": "99388494kdkj49939"
                        }}
                    }}
                    """

        return prompt

    def extract_info(self, email_data: dict) -> Union[dict, None]:
        """
        Extract candidate information from email content
        Returns None if not a job application, otherwise returns the info dictionary
        """
        print("inside extract_info")
        # Initialize default info dictionary
        info = {
            'email': None,
            'first_name': None,
            'last_name': None,
            'job_id': None,
            'phone': None,
            'current_company': None,
            'current_position': None,
            'years_of_experience': None
        }

        # Extract email first as we need it for notifications
        if email_data.get('from'):
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', email_data['from'])
            if email_match:
                info['email'] = email_match.group(0)

        print("my email data is ", json.dumps(email_data, indent=4))

        # Get LLM response
        prompt = self.format_email_for_llm(email_data)
        llm_response = self.__llmService.extract_info_from_email(prompt)

        print("llm response is : ",llm_response)

        # Return None if not a job application
        if not llm_response.get('is_job_application', False):
            return None

        # Extract initial data from LLM response
        extracted_info = llm_response.get('extracted_info', {})

        # Check for missing fields first
        if llm_response.get('has_missing_fields', True):
            self.__notificationService.sendJobApplicationNotificationFeedback(
                data=llm_response.get('missing_fields', []),
                recipient_email=info['email'],
                notification_type=NotificationType.MISSING_FIELDS
            )
            logging.warning(f"Missing fields detected: {llm_response.get('missing_fields', [])}")

        # Check if job exists in database
        if extracted_info.get('job_id'):
            job = self.__jobService.fetch_by_id_for_xml(extracted_info['job_id'])
            if job is None:
                self.__notificationService.sendJobApplicationNotificationFeedback(
                    data=f"Job ID {extracted_info['job_id']} not found in the system",
                    recipient_email=info['email'],
                    notification_type=NotificationType.JOB_NOT_FOUND
                )
                logging.warning(f"Failed to retrieve job: {extracted_info.get('job_id')}")
                return None  # Return None as we can't process without valid job ID

        # Populate info with extracted data
        if extracted_info:
            info['first_name'] = extracted_info.get('first_name') + " " + extracted_info.get('middle_name')
            info['last_name'] = extracted_info.get('last_name')
            info['job_id'] = extracted_info.get('job_id')

        print("infor extracted successfully: ", info)
        return info

    def create_xml(self, info: dict, document_filename: str) -> str:
        """Create XML with candidate information"""
        # Create root element
        root = ET.Element("candidate")

        # Add candidate information
        for key, value in info.items():
            if key != 'documents':
                elem = ET.SubElement(root, key)
                elem.text = str(value) if value is not None else ""

        # Add documents section
        documents = ET.SubElement(root, "documents")
        document = ET.SubElement(documents, "document")
        document.set("name", document_filename)
        document.set("type", "resume")
        document.text = document_filename

        # Create pretty XML string
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")

        return xml_str

    def process_email(self, email_data: dict, attachment_types) -> tuple:
        """Process email and generate XML"""
        try:
            # Extract information
            info = self.extract_info(email_data)

            print("validating the email attachments..")

            valid_attachments = [
                attachment for attachment in email_data['attachments']
                if os.path.splitext(attachment['original_filename'])[1].lower()
                   in attachment_types
            ]


            # Get the first attachment
            if not valid_attachments:
                self.__notificationService.sendJobApplicationNotificationFeedback(
                    data="",
                    recipient_email=info['email'],
                    notification_type=NotificationType.RESUME_NOT_FOUND
                )
                raise ValueError("No attachments found in email")

            attachment = email_data['attachments'][0]
            original_path = attachment['filepath']

            # Generate new filename with GUID
            file_ext = os.path.splitext(attachment['original_filename'])[1]
            new_filename = f"{str(uuid.uuid4())}{file_ext}"

            # Create XML content
            xml_content = self.create_xml(info, new_filename)

            # Generate XML filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            xml_filename = f"candidate_{timestamp}.xml"

            # Define new paths
            new_doc_path = os.path.join(self.watcher_folder, new_filename)
            xml_path = os.path.join(self.watcher_folder, xml_filename)

            # Move and rename the document
            shutil.move(original_path, new_doc_path)

            # Save XML file
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            return True, f"Successfully processed email and created {xml_filename}"

        except Exception as e:
            return False, f"Error processing email: {str(e)}"

    def cleanup_attachments(self, email_attachments_dir: str):
        """Clean up the attachments directory"""
        try:
            if os.path.exists(email_attachments_dir):
                shutil.rmtree(email_attachments_dir)
                os.makedirs(email_attachments_dir)
        except Exception as e:
            print(f"Error cleaning up attachments: {str(e)}")

class XMLProcessor:
    @staticmethod
    def parse_xml(xml_path: str) -> Tuple[Optional[CandidateDocument], Optional[str]]:
        try:
            logging.info(f"Starting to parse XML file: {xml_path}")
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Extract person info
            required_fields = ['email', 'first_name', 'last_name', 'job_id']
            optional_fields = ['phone', 'current_company', 'current_position', 'years_of_experience']

            # Validate required fields
            for field in required_fields:
                if root.find(field) is None or not root.find(field).text:
                    error_msg = f"Missing or empty required field: {field}"
                    logging.error(error_msg)
                    return None, error_msg

            # Process optional fields
            field_values = {}
            for field in optional_fields:
                element = root.find(field)
                field_values[field] = element.text if element is not None else None

            # Convert years_of_experience to int if present
            if field_values['years_of_experience']:
                try:
                    field_values['years_of_experience'] = int(field_values['years_of_experience'])
                except ValueError:
                    error_msg = "years_of_experience must be a valid integer"
                    logging.error(error_msg)
                    return None, error_msg

            person_info = PersonInfo(
                email=root.find('email').text,
                first_name=root.find('first_name').text,
                last_name=root.find('last_name').text,
                job_id=root.find('job_id').text,
                phone=field_values['phone'],
                current_company=field_values['current_company'],
                current_position=field_values['current_position'],
                years_of_experience=field_values['years_of_experience']
            )

            # Extract documents
            documents_elem = root.find('documents')
            if documents_elem is None:
                error_msg = "Missing documents section in XML"
                logging.error(error_msg)
                return None, error_msg

            documents = []
            for doc_elem in documents_elem.findall('document'):
                if not all(doc_elem.get(attr) for attr in ['name', 'type']):
                    error_msg = "Document missing required attributes (name, type)"
                    logging.error(error_msg)
                    return None, error_msg

                documents.append(DocumentInfo(
                    original_name=doc_elem.get('name'),
                    file_path=os.path.join(os.path.dirname(xml_path), doc_elem.text),
                    document_type=doc_elem.get('type')
                ))

            if not documents:
                error_msg = "No documents listed in XML"
                logging.error(error_msg)
                return None, error_msg

            return CandidateDocument(person_info, documents), None

        except ET.ParseError as e:
            error_msg = f"XML parsing error: {str(e)}"
            logging.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error while parsing XML: {str(e)}"
            logging.error(error_msg)
            logging.error(error_msg)
            return None, error_msg
