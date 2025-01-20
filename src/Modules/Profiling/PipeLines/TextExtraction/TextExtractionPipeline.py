from datetime import datetime
from typing import Dict, Any
from src.Helpers.PipelineMonitor import PipelineStatus
from src.Modules.Profiling.PipeLines.TextExtraction.LLMTextExtractionService import ResumeVisionParser
from src.config.DBModelsConfig import db
from src.Modules.Candidate.CandidateModels import Candidate
from src.Helpers.ErrorHandling import CustomError

class MonitoredTextExtractionPipeline:
    def __init__(self, monitor):
        self.resume_parser = None
        self.monitor = monitor

    def process_candidate(self, candidate_id: str) -> None:
        try:
            self.monitor.update_pipeline_state(
                "text_extraction",
                PipelineStatus.RUNNING,
                f"Processing candidate {candidate_id}"
            )

            candidate = Candidate.query.get(candidate_id)
            if not candidate or not candidate.resume_url:
                raise CustomError("Candidate or resume not found", 404)

            # Parse resume logic here...
            parser = ResumeVisionParser(candidate.resume_url)
            parsed_data = parser.parse_resume_with_vision()

            candidate.parsed_resume_data = parsed_data
            candidate.profiler_status = 'SCRAP'
            candidate.updated_at = datetime.utcnow()

            db.session.commit()

            self.monitor.update_pipeline_state(
                "text_extraction",
                PipelineStatus.IDLE,
                f"Successfully processed candidate {candidate_id}"
            )

        except Exception as e:
            db.session.rollback()
            self.monitor.update_pipeline_state(
                "text_extraction",
                PipelineStatus.ERROR,
                error_message=str(e)
            )
            raise CustomError(f"Error processing resume: {str(e)}", 400)

    def run_pipeline(self):
        try:
            self.monitor.update_pipeline_state(
                "text_extraction",
                PipelineStatus.RUNNING,
                "Starting text extraction pipeline"
            )

            candidates = Candidate.query.filter(
                Candidate.resume_url.isnot(None),
                Candidate.profiler_status.is_(None)
            ).all()

            for candidate in candidates:
                try:
                    self.process_candidate(candidate.id)
                except Exception as e:
                    print(f"Failed to process candidate {candidate.id}: {str(e)}")
                    continue

            self.monitor.update_pipeline_state(
                "text_extraction",
                PipelineStatus.IDLE,
                "Pipeline completed"
            )

        except Exception as e:
            self.monitor.update_pipeline_state(
                "text_extraction",
                PipelineStatus.ERROR,
                error_message=str(e)
            )
            raise CustomError(f"Pipeline execution failed: {str(e)}", 400)