import logging
from typing import List, Tuple, Optional
import os
import time
import shutil
from datetime import datetime

from flask import Flask
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.Candidate.Documents.DocumentService import DocumentService
from src.Modules.Candidate.Documents.DocumentModels import CandidateDocument, DocumentInfo, PersonInfo
import xml.etree.ElementTree as ET

from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor


class FileWatcherPipelineConfig(PipelineConfig):
    def __init__(self,
                 name: str = "file_watcher",
                 batch_size: int = 10,
                 process_interval: int = 60,
                 watch_folder: str = "",
                 failed_folder: str = "",
                 resume_path: str = "",):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.resume_path = resume_path
        self.watch_folder = os.path.abspath(watch_folder)
        self.failed_folder = os.path.abspath(failed_folder)

        # Create directories
        os.makedirs(self.watch_folder, exist_ok=True)
        os.makedirs(self.failed_folder, exist_ok=True)


class FileWatcherPipeline(BasePipeline):
    def __init__(self, app: Flask, config: FileWatcherPipelineConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: FileWatcherPipelineConfig = config
        self.processor = XMLProcessor()
        self.candidate_service = CandidateService()
        self.document_service = DocumentService(config.resume_path)

    def process_batch(self) -> None:
        """Process a batch of XML files"""
        try:
            # Look for XML files
            files = os.listdir(self.config.watch_folder)
            xml_files = [f for f in files if f.endswith('.xml')][:self.config.batch_size]

            if not xml_files:
                self.logger.info("No XML files found for processing")
                return

            self.logger.info(f"Found {len(xml_files)} XML files to process")

            for filename in xml_files:
                xml_path = os.path.join(self.config.watch_folder, filename)
                try:
                    self._process_single_file(xml_path)
                except Exception as e:
                    self.logger.error(f"Error processing file {filename}: {str(e)}")
                    self._move_to_failed(xml_path, str(e))

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            self.monitor.update_state(
                self.config.name,
                PipelineStatus.ERROR,
                error_message=f"Batch processing failed: {str(e)}"
            )

    def _process_single_file(self, xml_path: str) -> None:
        """Process a single XML file"""
        self.logger.info(f"Processing file: {os.path.basename(xml_path)}")

        # Parse XML
        document, parse_error = self.processor.parse_xml(xml_path)
        if parse_error:
            raise ValueError(f"XML parsing failed: {parse_error}")

        # Find and validate documents
        found_files, missing_files = self._find_documents(document)
        if missing_files:
            raise ValueError(f"Missing documents: {', '.join(missing_files)}")

        # Store in database
        success = self._store_in_database(document, found_files)
        if not success:
            raise ValueError("Failed to store in database")

        # Cleanup processed files
        self._cleanup_files(xml_path, found_files)

        self.logger.info(f"Successfully processed {os.path.basename(xml_path)}")

    def _find_documents(self, document: CandidateDocument) -> Tuple[List[str], List[str]]:
        """Find all required documents"""
        found_files = []
        missing_files = []

        for doc in document.documents:
            full_path = os.path.join(self.config.watch_folder, os.path.basename(doc.file_path))
            if os.path.exists(full_path):
                found_files.append(full_path)
            else:
                missing_files.append(os.path.basename(doc.file_path))

        return found_files, missing_files

    def _store_in_database(self, document: CandidateDocument, found_files: List[str]) -> bool:
        """Store candidate and document information in database"""
        try:
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
            for doc in document.documents:
                if doc.file_path in found_files:
                    self.document_service.store_document(
                        file_path=doc.file_path,
                        original_filename=doc.original_name,
                        candidate_id=created_candidate['id'],
                        document_type=doc.document_type
                    )

            return True

        except Exception as e:
            self.logger.error(f"Database storage error: {str(e)}")
            return False

    def _cleanup_files(self, xml_path: str, document_paths: List[str]) -> None:
        """Delete processed files"""
        try:
            os.remove(xml_path)
            for doc_path in document_paths:
                os.remove(doc_path)
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def _move_to_failed(self, xml_path: str, reason: str, found_documents: List[str] = None) -> None:
        """Move failed files to the failed folder"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            xml_name = os.path.splitext(os.path.basename(xml_path))[0]
            failed_subfolder = os.path.join(self.config.failed_folder, f"{xml_name}_{timestamp}")
            os.makedirs(failed_subfolder, exist_ok=True)

            # Move XML file
            shutil.move(xml_path, os.path.join(failed_subfolder, os.path.basename(xml_path)))

            # Write failure reason
            with open(os.path.join(failed_subfolder, "failure_reason.txt"), 'w') as f:
                f.write(f"Failure Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Reason: {reason}\n")

            # Move associated documents
            if found_documents:
                for doc_path in found_documents:
                    if os.path.exists(doc_path):
                        shutil.move(doc_path, os.path.join(failed_subfolder, os.path.basename(doc_path)))

        except Exception as e:
            self.logger.error(f"Error moving files to failed folder: {str(e)}")

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


# from flask import Flask
# from src.Modules.PipelineTracking.PipelineTrackingService import PipelineTrackingService
# from src.Modules.PipelineTracking.PipelineTrackingModels import PipelineStage, PipelineStatus
# from src.Modules.PipeLines.Profiling.PipeLineBase import BasePipeline
#
#
# class FileWatcherPipeline(BasePipeline):
#     def process_batch(self) -> None:
#         try:
#             # Get pipeline trackings for FILE_WATCHER stage
#             pipeline_trackings = self._get_candidates_for_processing(
#                 PipelineStage.FILE_WATCHER
#             )
#
#             for pipeline_tracking in pipeline_trackings:
#                 try:
#                     pipeline_id = pipeline_tracking['id']
#
#                     # Mark pipeline as in progress
#                     self._update_pipeline_tracking(
#                         pipeline_id,
#                         PipelineStage.FILE_WATCHER,
#                         PipelineStatus.IN_PROGRESS
#                     )
#
#                     # Look for XML files to process
#                     files = os.listdir(self.config.watch_folder)
#                     xml_files = [f for f in files if f.endswith('.xml')]
#
#                     if not xml_files:
#                         # No files to process, mark as skipped
#                         self._update_pipeline_tracking(
#                             pipeline_id,
#                             PipelineStage.FILE_WATCHER,
#                             PipelineStatus.SKIPPED
#                         )
#                         continue
#
#                     # Process XML file
#                     self._process_single_file(
#                         os.path.join(self.config.watch_folder, xml_files[0]),
#                         pipeline_tracking
#                     )
#
#                     # Mark pipeline as successful
#                     self._update_pipeline_tracking(
#                         pipeline_id,
#                         PipelineStage.FILE_WATCHER,
#                         PipelineStatus.SUCCESSFUL
#                     )
#
#                 except Exception as e:
#                     # Handle individual pipeline processing errors
#                     self._process_pipeline_error(
#                         pipeline_tracking['id'],
#                         PipelineStage.FILE_WATCHER,
#                         e
#                     )
#
#         except Exception as e:
#             self.logger.error(f"Batch processing failed: {str(e)}")