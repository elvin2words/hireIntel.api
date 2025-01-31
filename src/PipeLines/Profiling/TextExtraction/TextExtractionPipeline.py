import os

from flask import Flask
from datetime import datetime
from src.Modules.Candidate.CandidateModels import Candidate, CandidateStatus, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.Candidate.Documents.DocumentService import DocumentService
from src.Modules.PipeLineData.TextExtractionData.TextExtractionService import ResumeService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.TextExtraction.LLMTextExtractionService import ResumeVisionParser
from src.config.DBModelsConfig import db
from src.Helpers.ErrorHandling import CustomError

class TextExtractionPipelineConfig(PipelineConfig):
    def __init__(self,
                 name: str = "file_watcher",
                 batch_size: int = 10,
                 process_interval: int = 60,
                 resume_path: str = "",
                 json_resume_path: str = "",):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.resume_path = os.path.abspath(resume_path)
        self.json_resume_path = os.path.abspath(json_resume_path)

        os.makedirs(self.resume_path, exist_ok=True)
        os.makedirs(self.json_resume_path, exist_ok=True)


class TextExtractionPipeline(BasePipeline):
    def __init__(self, app: Flask, config: TextExtractionPipelineConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.__document_service = DocumentService(config.resume_path)
        self.__candidate_service = CandidateService()
        self.__resume_service = ResumeService()
        self.config: TextExtractionPipelineConfig = config

    def process_batch(self):
        try:
            # Find candidates that need processing
            candidates = (Candidate.query
                          .filter(
                Candidate.status == CandidateStatus.APPLIED,
                Candidate.pipeline_status.is_(CandidatePipelineStatus.EXTRACT_TEXT)
            )
                          .limit(self.config.batch_size)
                          .all())

            if not candidates:
                self.logger.info("No candidates found for processing")
                return

            self.logger.info(f"Processing {len(candidates)} candidates")

            for candidate in candidates:
                try:
                    self._process_candidate(candidate.id)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process candidate {candidate.id}: {str(e)}"
                    )
                    self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate.id)

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise

    def _process_candidate(self, candidate_id: str) -> None:
        """Process a single candidate's documents with comprehensive pipeline status updates"""
        try:
            self.logger.info(f"Starting processing for candidate ID: {candidate_id}")

            # Set initial processing status
            self.__candidate_service.set_pipeline_status_to_text_extraction(candidate_id)

            self.monitor.update_state(
                "text_extraction",
                PipelineStatus.RUNNING,
                message=f"Processing documents for candidate {candidate_id}"
            )

            # Get the candidate
            candidate = Candidate.query.get(candidate_id)

            if not isinstance(candidate_id, str):
                self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate_id)
                raise ValueError(f"candidate_id must be a string, got {type(candidate_id)}")

            if not candidate:
                self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate_id)
                self.logger.error(f"Candidate not found: {candidate_id}")
                raise CustomError("Candidate not found", 404)

            self.logger.info(f"Found candidate: {candidate.email}")

            # Get candidate's resume document
            try:
                self.logger.info(f"Fetching resume for candidate: {candidate.email}")
                resume = self.__document_service.get_candidate_resume(candidate_id)
                if not resume:
                    self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate_id)
                    self.logger.error(f"No resume found for candidate: {candidate.email}")
                    raise CustomError("No resume found for candidate", 404)
                self.logger.info(f"Successfully retrieved resume document ID: {resume.id}")
            except Exception as e:
                self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate_id)
                self.logger.error(f"Error fetching resume for candidate {candidate.email}: {str(e)}")
                raise

            try:
                # Extract text from resume
                self.logger.info(f"Starting text extraction for resume ID: {resume.id}")
                parser = ResumeVisionParser(resume.file_path, self.config.json_resume_path)
                extracted_text = parser.parse_resume_with_vision()
                self.logger.info(f"Text extraction completed. Extracted {len(extracted_text)} characters")

                # Update candidate with extracted text
                self.logger.info(f"Updating database record for candidate: {candidate.email}")
                candidate.parsed_resume_data = {
                    'extracted_text': extracted_text,
                    'extraction_date': datetime.utcnow().isoformat(),
                    'document_id': resume.id
                }

                # Save the extracted text to the database
                self.__resume_service.create_resume(extracted_text)


                # Log sample of extracted text
                text_preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                self.logger.info(f"Text preview: {text_preview}")

                db.session.commit()
                self.logger.info(f"Successfully updated database for candidate: {candidate.email}")

                # Update pipeline status to next stage after successful processing
                self.__candidate_service.set_pipeline_status_to_google_scrape(candidate_id)

                self.monitor.update_state(
                    "text_extraction",
                    PipelineStatus.IDLE,
                    message=f"Successfully processed candidate {candidate_id}"
                )

            except Exception as e:
                self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate_id)
                self.logger.error(f"Error processing resume for candidate {candidate.email}: {str(e)}")
                db.session.rollback()
                self.monitor.update_state(
                    "text_extraction",
                    PipelineStatus.ERROR,
                    message=f"Failed to process resume",
                    error_message=str(e)
                )
                raise

        except Exception as e:
            self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate_id)
            self.logger.error(f"Pipeline error for candidate {candidate_id}: {str(e)}")
            db.session.rollback()
            self.monitor.update_state(
                "text_extraction",
                PipelineStatus.ERROR,
                message="Pipeline error",
                error_message=str(e)
            )
            raise CustomError(f"Error processing candidate: {str(e)}", 400)