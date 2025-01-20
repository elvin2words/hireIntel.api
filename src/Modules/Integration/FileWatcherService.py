import os
import time
import xml.etree.ElementTree as ET
import shutil
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import logging

from src.Helpers.PipelineMonitor import PipelineMonitor, PipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.Candidate.Documents.DocumentModels import Document, PersonInfo, DocumentInfo, CandidateDocument
from src.Modules.Candidate.Documents.DocumentService import DocumentService

# Interval mapping (minutes to seconds)
INTERVAL_MAPPING: Dict[int, int] = {
    1: 60,    # 1 minute = 60 seconds
    2: 120,   # 2 minutes = 120 seconds
    3: 180,   # 3 minutes = 180 seconds
    4: 240,   # 4 minutes = 240 seconds
    5: 300    # 5 minutes = 300 seconds
}

class ConfigManager:
    def __init__(self, watch_folder: str, failed_folder: str, check_interval: int):
        """
        Initialize ConfigManager
        :param watch_folder: Path to watch folder
        :param failed_folder: Path to failed folder
        :param check_interval: Interval in minutes (1-5)
        """
        self.watch_folder = os.path.abspath(watch_folder)
        self.failed_folder = os.path.abspath(failed_folder)

        # Convert minutes to seconds using mapping
        if check_interval not in INTERVAL_MAPPING:
            raise ValueError(f"Check interval must be between 1-5 minutes. Got: {check_interval}")

        self.check_interval = INTERVAL_MAPPING[check_interval]

        # Create directories if they don't exist
        os.makedirs(self.watch_folder, exist_ok=True)
        os.makedirs(self.failed_folder, exist_ok=True)
        logging.info(f"Initialized watch folder at: {self.watch_folder}")
        logging.info(f"Initialized failed folder at: {self.failed_folder}")
        logging.info(f"Check interval set to: {check_interval} minutes ({self.check_interval} seconds)")


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


class DatabaseHandler:
    def __init__(self, app):
        self.app = app
        self.candidate_service = CandidateService()
        self.document_service = DocumentService()

    def store_in_database(self, document: CandidateDocument, found_files: List[str]) -> Tuple[bool, Optional[str]]:
        """Store candidate and document information in database"""
        try:
            logging.info("Attempting to store candidate information in database...")

            with self.app.app_context():
                # Prepare candidate data
                candidate_data = {
                    'email': document.person_info.email,
                    'first_name': document.person_info.first_name,
                    'last_name': document.person_info.last_name,
                    'job_id': document.person_info.job_id,
                    'phone': document.person_info.phone,
                    'current_company': document.person_info.current_company,
                    'current_position': document.person_info.current_position,
                    'years_of_experience': document.person_info.years_of_experience,
                }

                # Create candidate
                created_candidate = self.candidate_service.create_candidate(candidate_data)

                # Store documents
                stored_documents = []
                for doc in document.documents:
                    if doc.file_path in found_files:
                        stored_document = self.document_service.store_document(
                            file_path=doc.file_path,
                            original_filename=doc.original_name,
                            candidate_id=created_candidate['id'],
                            document_type=doc.document_type
                        )
                        stored_documents.append(stored_document)

                logging.info(f"Successfully created candidate with ID: {created_candidate['id']}")
                logging.info(f"Stored {len(stored_documents)} documents")

                return True, None

        except Exception as e:
            error_msg = f"Database storage error: {str(e)}"
            logging.error(error_msg)
            return False, error_msg

# Allows you to monitor health of file watcher
class MonitoredFileWatcher:
    def __init__(self, app, config, monitor):
        self.app = app
        self.config = config
        self.monitor = monitor
        self.processor = XMLProcessor()
        self.db_handler = DatabaseHandler(app)

    def cleanup_files(self, xml_path: str, document_paths: List[str]):
        """Delete processed files"""
        try:
            logging.info("Starting cleanup of processed files...")
            os.remove(xml_path)
            logging.info(f"Removed XML file: {os.path.basename(xml_path)}")
            for doc_path in document_paths:
                os.remove(doc_path)
                logging.info(f"Removed document: {os.path.basename(doc_path)}")
            logging.info("Cleanup completed successfully")
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

    def find_documents(self, document_names: List[str]) -> Tuple[List[str], List[str]]:
        """Find all specified documents in the watch folder and return found and missing files"""
        logging.info("Starting to search for referenced documents...")
        found_files = []
        missing_files = []
        for doc_name in document_names:
            full_path = os.path.join(self.config.watch_folder, doc_name)
            if os.path.exists(full_path):
                logging.info(f"Found document: {doc_name}")
                found_files.append(full_path)
            else:
                logging.warning(f"Missing document: {doc_name}")
                missing_files.append(doc_name)
        return found_files, missing_files

    def move_to_failed(self, xml_path: str, reason: str, found_documents: List[str] = None):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            xml_name = os.path.splitext(os.path.basename(xml_path))[0]
            failed_subfolder = os.path.join(self.config.failed_folder, f"{xml_name}_{timestamp}")
            os.makedirs(failed_subfolder, exist_ok=True)

            failed_xml_path = os.path.join(failed_subfolder, os.path.basename(xml_path))
            shutil.move(xml_path, failed_xml_path)
            logging.warning(f"Moved {os.path.basename(xml_path)} to failed folder")

            reason_file = os.path.join(failed_subfolder, "failure_reason.txt")
            with open(reason_file, 'w') as f:
                f.write(f"Failure Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Reason: {reason}\n")

            if found_documents:
                for doc_path in found_documents:
                    if os.path.exists(doc_path):
                        failed_doc_path = os.path.join(failed_subfolder, os.path.basename(doc_path))
                        shutil.move(doc_path, failed_doc_path)
                        logging.warning(f"Moved associated document to failed folder: {os.path.basename(doc_path)}")

            logging.warning(f"Failure reason: {reason}")
            logging.info(f"All failed files moved to: {failed_subfolder}")

        except Exception as e:
            logging.error(f"Error moving files to failed folder: {str(e)}")

    def process_xml_file(self, xml_path: str) -> bool:
        """Process a single XML file with monitoring"""
        try:
            with self.app.app_context():
                self.monitor.update_pipeline_state(
                    "file_watcher",
                    PipelineStatus.RUNNING,
                    f"Processing XML file: {os.path.basename(xml_path)}",
                    details={'file': os.path.basename(xml_path)}
                )

                # Parse XML
                document, parse_error = self.processor.parse_xml(xml_path)
                if not document:
                    self.monitor.update_pipeline_state(
                        "file_watcher",
                        PipelineStatus.ERROR,
                        error_message=f"XML parsing failed: {parse_error}"
                    )
                    self.move_to_failed(xml_path, f"XML parsing failed: {parse_error}")
                    return False

                # Find documents
                self.monitor.update_pipeline_state(
                    "file_watcher",
                    PipelineStatus.RUNNING,
                    "Checking for required documents"
                )

                found_files, missing_files = self.find_documents([doc.file_path for doc in document.documents])
                if missing_files:
                    failure_reason = f"Missing documents: {', '.join(missing_files)}"
                    self.monitor.update_pipeline_state(
                        "file_watcher",
                        PipelineStatus.ERROR,
                        error_message=failure_reason
                    )
                    self.move_to_failed(xml_path, failure_reason, found_files)
                    return False

                # Store in database
                self.monitor.update_pipeline_state(
                    "file_watcher",
                    PipelineStatus.RUNNING,
                    "Storing data in database"
                )

                success, db_error = self.db_handler.store_in_database(document, found_files)
                if not success:
                    self.monitor.update_pipeline_state(
                        "file_watcher",
                        PipelineStatus.ERROR,
                        error_message=f"Database storage failed: {db_error}"
                    )
                    self.move_to_failed(xml_path, f"Database storage failed: {db_error}", found_files)
                    return False

                # Cleanup
                self.cleanup_files(xml_path, found_files)

                self.monitor.update_pipeline_state(
                    "file_watcher",
                    PipelineStatus.IDLE,
                    f"Successfully processed {os.path.basename(xml_path)}"
                )

                return True

        except Exception as e:
            self.monitor.update_pipeline_state(
                "file_watcher",
                PipelineStatus.ERROR,
                error_message=f"Error processing file: {str(e)}"
            )
            return False

    def watch(self):
        """Main watching loop with monitoring"""
        with self.app.app_context():
            self.monitor.update_pipeline_state(
                "file_watcher",
                PipelineStatus.RUNNING,
                "Starting file watcher"
            )

            while True:
                try:
                    # Look for XML files
                    files = os.listdir(self.config.watch_folder)
                    xml_files = [f for f in files if f.endswith('.xml')]

                    with self.app.app_context():
                        self.monitor.update_pipeline_state(
                            "file_watcher",
                            PipelineStatus.RUNNING,
                            f"Found {len(xml_files)} XML files to process",
                            details={'files_found': len(xml_files)}
                        )

                    for filename in xml_files:
                        xml_path = os.path.join(self.config.watch_folder, filename)
                        self.process_xml_file(xml_path)

                    # Update state before waiting
                    with self.app.app_context():
                        self.monitor.update_pipeline_state(
                            "file_watcher",
                            PipelineStatus.IDLE,
                            f"Waiting {self.config.check_interval} seconds before next check"
                        )

                    time.sleep(self.config.check_interval)

                except Exception as e:
                    with self.app.app_context():
                        self.monitor.update_pipeline_state(
                            "file_watcher",
                            PipelineStatus.ERROR,
                            error_message=f"Error in watch loop: {str(e)}"
                        )
                    time.sleep(self.config.check_interval)