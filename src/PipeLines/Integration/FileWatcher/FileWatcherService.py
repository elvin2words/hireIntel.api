from typing import List, Tuple, Optional, Dict
import os
import time
import shutil
from datetime import datetime
from flask import Flask
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.Candidate.Documents.DocumentService import DocumentService
from src.Modules.Candidate.Documents.DocumentModels import CandidateDocument
from src.PipeLines.Integration.EmailWatcher.EmailProccessor import XMLProcessor
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor



class FileWatcherPipelineConfig(PipelineConfig):
    def __init__(self,
                 name: str = "file_watcher",
                 batch_size: int = 10,
                 process_interval: int = 60,
                 watch_folder: str = "",
                 failed_folder: str = "",
                 resume_path: str = ""):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.resume_path = resume_path
        self.watch_folder = os.path.abspath(watch_folder)
        self.failed_folder = os.path.abspath(failed_folder)

        os.makedirs(self.watch_folder, exist_ok=True)
        os.makedirs(self.failed_folder, exist_ok=True)


class FileWatcherPipeline(BasePipeline):
    def __init__(self, app: Flask, config: FileWatcherPipelineConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: FileWatcherPipelineConfig = config
        self.processor = XMLProcessor()
        self.candidate_service = CandidateService()
        self.document_service = DocumentService(config.resume_path)

    def get_input_data(self) -> List[Dict[str, str]]:
        """Find XML files in watch folder"""
        files = os.listdir(self.config.watch_folder)
        xml_files = [f for f in files if f.endswith('.xml')][:self.config.batch_size]
        return [{'path': os.path.join(self.config.watch_folder, f)} for f in xml_files]

    def process_item(self, item: Dict[str, str]) -> Optional[Dict]:
        """Process a single XML file"""
        xml_path = item['path']

        # Parse XML
        document, parse_error = self.processor.parse_xml(xml_path)
        if parse_error:
            raise ValueError(f"XML parsing failed: {parse_error}")

        # Find and validate documents
        found_files, missing_files = self._find_documents(document)
        if missing_files:
            raise ValueError(f"Missing documents: {', '.join(missing_files)}")

        return {
            'xml_path': xml_path,
            'document': document,
            'found_files': found_files
        }

    def update_output(self, results: List[Dict]) -> None:
        """Store processed documents in database and cleanup files"""
        for result in results:
            if not result:
                continue

            success = self._store_in_database(result['document'], result['found_files'])
            if success:
                self._cleanup_files(result['xml_path'], result['found_files'])

    def handle_item_failure(self, item: Dict[str, str], error: Exception) -> None:
        """Move failed files to failed folder"""
        xml_path = item['path']
        self.logger.error(f"Error processing file {os.path.basename(xml_path)}: {str(error)}")
        self._move_to_failed(xml_path, str(error))

    def _find_documents(self, document: CandidateDocument) -> Tuple[List[str], List[str]]:
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
        try:
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

            created_candidate = self.candidate_service.create_candidate(candidate_data)

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
        try:
            os.remove(xml_path)
            for doc_path in document_paths:
                os.remove(doc_path)
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    def _move_to_failed(self, xml_path: str, reason: str, found_documents: List[str] = None) -> None:
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            xml_name = os.path.splitext(os.path.basename(xml_path))[0]
            failed_subfolder = os.path.join(self.config.failed_folder, f"{xml_name}_{timestamp}")
            os.makedirs(failed_subfolder, exist_ok=True)

            shutil.move(xml_path, os.path.join(failed_subfolder, os.path.basename(xml_path)))

            with open(os.path.join(failed_subfolder, "failure_reason.txt"), 'w') as f:
                f.write(f"Failure Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Reason: {reason}\n")

            if found_documents:
                for doc_path in found_documents:
                    if os.path.exists(doc_path):
                        shutil.move(doc_path, os.path.join(failed_subfolder, os.path.basename(doc_path)))

        except Exception as e:
            self.logger.error(f"Error moving files to failed folder: {str(e)}")

# import logging
# from typing import List, Tuple, Optional
# import os
# import time
# import shutil
# from datetime import datetime
#
# from flask import Flask
# from src.Modules.Candidate.CandidateService import CandidateService
# from src.Modules.Candidate.Documents.DocumentService import DocumentService
# from src.Modules.Candidate.Documents.DocumentModels import CandidateDocument, DocumentInfo, PersonInfo
# import xml.etree.ElementTree as ET
#
# from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
# from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
# from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
#
#
# class FileWatcherPipelineConfig(PipelineConfig):
#     def __init__(self,
#                  name: str = "file_watcher",
#                  batch_size: int = 10,
#                  process_interval: int = 60,
#                  watch_folder: str = "",
#                  failed_folder: str = "",
#                  resume_path: str = "",):
#         super().__init__(name, batch_size, process_interval=process_interval)
#         self.resume_path = resume_path
#         self.watch_folder = os.path.abspath(watch_folder)
#         self.failed_folder = os.path.abspath(failed_folder)
#
#         # Create directories
#         os.makedirs(self.watch_folder, exist_ok=True)
#         os.makedirs(self.failed_folder, exist_ok=True)
#
#
# class FileWatcherPipeline(BasePipeline):
#     def __init__(self, app: Flask, config: FileWatcherPipelineConfig, monitor: PipelineMonitor):
#         super().__init__(app, config, monitor)
#         self.config: FileWatcherPipelineConfig = config
#         self.processor = XMLProcessor()
#         self.candidate_service = CandidateService()
#         self.document_service = DocumentService(config.resume_path)
#
#     def process_batch(self) -> None:
#         """Process a batch of XML files"""
#         try:
#             # Look for XML files
#             files = os.listdir(self.config.watch_folder)
#             xml_files = [f for f in files if f.endswith('.xml')][:self.config.batch_size]
#
#             if not xml_files:
#                 self.logger.info("No XML files found for processing")
#                 return
#
#             self.logger.info(f"Found {len(xml_files)} XML files to process")
#
#             for filename in xml_files:
#                 xml_path = os.path.join(self.config.watch_folder, filename)
#                 try:
#                     self._process_single_file(xml_path)
#                 except Exception as e:
#                     self.logger.error(f"Error processing file {filename}: {str(e)}")
#                     self._move_to_failed(xml_path, str(e))
#
#         except Exception as e:
#             self.logger.error(f"Batch processing failed: {str(e)}")
#             self.monitor.update_state(
#                 self.config.name,
#                 PipelineStatus.ERROR,
#                 error_message=f"Batch processing failed: {str(e)}"
#             )
#
#     def _process_single_file(self, xml_path: str) -> None:
#         """Process a single XML file"""
#         self.logger.info(f"Processing file: {os.path.basename(xml_path)}")
#
#         # Parse XML
#         document, parse_error = self.processor.parse_xml(xml_path)
#         if parse_error:
#             raise ValueError(f"XML parsing failed: {parse_error}")
#
#         # Find and validate documents
#         found_files, missing_files = self._find_documents(document)
#         if missing_files:
#             raise ValueError(f"Missing documents: {', '.join(missing_files)}")
#
#         # Store in database
#         success = self._store_in_database(document, found_files)
#         if not success:
#             raise ValueError("Failed to store in database")
#
#         # Cleanup processed files
#         self._cleanup_files(xml_path, found_files)
#
#         self.logger.info(f"Successfully processed {os.path.basename(xml_path)}")
#
#     def _find_documents(self, document: CandidateDocument) -> Tuple[List[str], List[str]]:
#         """Find all required documents"""
#         found_files = []
#         missing_files = []
#
#         for doc in document.documents:
#             full_path = os.path.join(self.config.watch_folder, os.path.basename(doc.file_path))
#             if os.path.exists(full_path):
#                 found_files.append(full_path)
#             else:
#                 missing_files.append(os.path.basename(doc.file_path))
#
#         return found_files, missing_files
#
#     def _store_in_database(self, document: CandidateDocument, found_files: List[str]) -> bool:
#         """Store candidate and document information in database"""
#         try:
#             # Prepare candidate data
#             candidate_data = {
#                 'email': document.person_info.email,
#                 'first_name': document.person_info.first_name,
#                 'last_name': document.person_info.last_name,
#                 'job_id': document.person_info.job_id,
#                 'phone': document.person_info.phone,
#                 'current_company': document.person_info.current_company,
#                 'current_position': document.person_info.current_position,
#                 'years_of_experience': document.person_info.years_of_experience,
#             }
#
#             # Create candidate
#             created_candidate = self.candidate_service.create_candidate(candidate_data)
#
#             # Store documents
#             for doc in document.documents:
#                 if doc.file_path in found_files:
#                     self.document_service.store_document(
#                         file_path=doc.file_path,
#                         original_filename=doc.original_name,
#                         candidate_id=created_candidate['id'],
#                         document_type=doc.document_type
#                     )
#
#             return True
#
#         except Exception as e:
#             self.logger.error(f"Database storage error: {str(e)}")
#             return False
#
#     def _cleanup_files(self, xml_path: str, document_paths: List[str]) -> None:
#         """Delete processed files"""
#         try:
#             os.remove(xml_path)
#             for doc_path in document_paths:
#                 os.remove(doc_path)
#         except Exception as e:
#             self.logger.error(f"Error during cleanup: {str(e)}")
#
#     def _move_to_failed(self, xml_path: str, reason: str, found_documents: List[str] = None) -> None:
#         """Move failed files to the failed folder"""
#         try:
#             timestamp = time.strftime("%Y%m%d_%H%M%S")
#             xml_name = os.path.splitext(os.path.basename(xml_path))[0]
#             failed_subfolder = os.path.join(self.config.failed_folder, f"{xml_name}_{timestamp}")
#             os.makedirs(failed_subfolder, exist_ok=True)
#
#             # Move XML file
#             shutil.move(xml_path, os.path.join(failed_subfolder, os.path.basename(xml_path)))
#
#             # Write failure reason
#             with open(os.path.join(failed_subfolder, "failure_reason.txt"), 'w') as f:
#                 f.write(f"Failure Timestamp: {datetime.now().isoformat()}\n")
#                 f.write(f"Reason: {reason}\n")
#
#             # Move associated documents
#             if found_documents:
#                 for doc_path in found_documents:
#                     if os.path.exists(doc_path):
#                         shutil.move(doc_path, os.path.join(failed_subfolder, os.path.basename(doc_path)))
#
#         except Exception as e:
#             self.logger.error(f"Error moving files to failed folder: {str(e)}")
#

