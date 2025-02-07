from flask import Flask
from typing import List, Optional, Dict
from datetime import datetime
import os

from src.Helpers.LLMService import LLMService
from src.Modules.Candidate.CandidateModels import Candidate, CandidateStatus, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.Candidate.Documents.DocumentService import DocumentService
from src.Modules.PipeLineData.TextExtractionData.TextExtractionService import TextExtractionDataService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.config.DBModelsConfig import db
from src.Helpers.ErrorHandling import CustomError


class TextExtractionPipelineConfig(PipelineConfig):
    def __init__(self,
                 name: str = "file_watcher",
                 batch_size: int = 10,
                 process_interval: int = 60,
                 resume_path: str = "",
                 json_resume_path: str = ""):
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
        self.__llmService = LLMService()
        self.__textExtractionDataService = TextExtractionDataService()
        self.config: TextExtractionPipelineConfig = config

    def get_input_data(self) -> List[Candidate]:
        return (Candidate.query
                .filter(
            Candidate.status == CandidateStatus.APPLIED,
            Candidate.pipeline_status.is_(CandidatePipelineStatus.XML)
        )
                .limit(self.config.batch_size)
                .all())

    def process_item(self, candidate: Candidate) -> Optional[Dict]:
        if not isinstance(candidate.id, str):
            raise ValueError(f"candidate_id must be a string, got {type(candidate.id)}")

        resume = self.__document_service.get_candidate_resume(candidate.id)
        if not resume:
            raise CustomError(f"No resume found for candidate {candidate.email}", 404)

        extracted_text = self.__llmService.parse_resume_with_vision(resume.file_path)

        return {
            'candidate_id': candidate.id,
            'extracted_text': extracted_text,
            'extraction_date': datetime.utcnow().isoformat(),
            'document_id': resume.id
        }

    def update_output(self, results: List[Dict]) -> None:
        for result in results:
            if not result:
                continue

            try:
                self.__textExtractionDataService.create_resume(
                    result['extracted_text'],
                    result['candidate_id']
                )
                self.__candidate_service.set_pipeline_status_to_google_scrape(
                    result['candidate_id']
                )
            except Exception as e:
                self.logger.error(f"Failed to save result for candidate {result['candidate_id']}: {str(e)}")
                self.__candidate_service.set_pipeline_status_to_text_extraction_failed(result['candidate_id'])
                continue

    def handle_item_failure(self, candidate: Candidate, error: Exception) -> None:
        self.logger.error(f"Text extraction failed for candidate {candidate.id}: {str(error)}")
        self.__candidate_service.set_pipeline_status_to_text_extraction_failed(candidate.id)
        db.session.rollback()