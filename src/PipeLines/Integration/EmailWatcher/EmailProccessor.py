import logging
import os
import uuid
import shutil
import xml.etree.ElementTree as ET
from typing import Tuple, Optional
from xml.dom import minidom
from datetime import datetime
import re

from src.Modules.Candidate.Documents.DocumentModels import DocumentInfo, CandidateDocument, PersonInfo


class EmailProcessor:
    def __init__(self, watcher_folder="./src/PipeLines/Integration/FileWatcher/Watcher/watcher_folder"):
        self.watcher_folder = watcher_folder
        # Create watcher folder if it doesn't exist
        os.makedirs(self.watcher_folder, exist_ok=True)

    def extract_info(self, email_data: dict) -> dict:
        """Extract candidate information from email content"""
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

        # Extract email from 'from' field
        if email_data['from']:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', email_data['from'])
            if email_match:
                info['email'] = email_match.group(0)

        # Extract names from 'from' field
        if email_data['from']:
            name_match = re.match(r'([^<]+)', email_data['from'])
            if name_match:
                full_name = name_match.group(1).strip().split()
                if len(full_name) >= 1:
                    info['first_name'] = full_name[0]
                if len(full_name) >= 2:
                    info['last_name'] = full_name[-1]

        # Generate a random job_id if none found
        info['job_id'] = str(uuid.uuid4())

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

    def process_email(self, email_data: dict) -> tuple:
        """Process email and generate XML"""
        try:
            # Extract information
            info = self.extract_info(email_data)

            # Get the first attachment
            if not email_data['attachments']:
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
