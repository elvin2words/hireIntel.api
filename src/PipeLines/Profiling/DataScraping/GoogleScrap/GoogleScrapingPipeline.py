from flask import Flask
from datetime import datetime
from typing import Dict, Any, List
import json
import requests
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.config.DBModelsConfig import db
from src.Helpers.ErrorHandling import CustomError


class GoogleScrapingConfig(PipelineConfig):
    def __init__(self,
                 name: str = "google_scraping",
                 batch_size: int = 10,
                 process_interval: int = 300,
                 api_key: str = "",
                 google_url: str = "https://google.serper.dev/search"):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.api_key = api_key
        self.google_url = google_url


class GoogleScrapingPipeline(BasePipeline):
    def __init__(self, app: Flask, config: GoogleScrapingConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: GoogleScrapingConfig = config
        self.headers = {
            'X-API-KEY': config.api_key,
            'Content-Type': 'application/json'
        }
        self.__candidate_service = CandidateService()

    def process_batch(self):
        """Process a batch of candidates for Google scraping"""
        try:
            # Find candidates that need Google scraping
            candidates = (Candidate.query
                          .filter_by(pipeline_status=CandidatePipelineStatus.GOOGLE_SCRAPE)
                          .limit(self.config.batch_size)
                          .all())

            if not candidates:
                self.logger.info("No candidates found for Google scraping")
                return

            self.logger.info(f"Processing {len(candidates)} candidates for Google scraping")

            for candidate in candidates:
                try:
                    self._process_candidate(candidate)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process Google data for candidate {candidate.id}: {str(e)}"
                    )
                    self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise

    def _search_candidate(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform Google search for candidate information"""
        try:
            # Extract search terms from parsed data
            personal_info = parsed_data.get('personal_information', {})
            name = personal_info.get('full_name', '')
            if not name:
                raise CustomError("No candidate name found in parsed data", 400)

            # Get most recent company if available
            work_experience = parsed_data.get('work_experience', [])
            company = work_experience[0].get('company', '') if work_experience else None

            # Construct search query
            keyword = f"{name}"
            if company:
                keyword += f" {company}"

            # Add technical context
            skills = parsed_data.get('skills', {})
            top_skills = (
                    skills.get('programming_languages', [])[:2] +
                    skills.get('frameworks_libraries', [])[:2]
            )
            if top_skills:
                keyword += f" developer {' '.join(top_skills)}"

            self.logger.info(f"Executing Google search with query: {keyword}")

            # Execute search
            payload = json.dumps({"q": keyword})
            response = requests.post(
                self.config.google_url,
                headers=self.headers,
                data=payload,
                timeout=30
            )
            response.raise_for_status()

            # Parse results
            data = response.json()
            results = []

            if 'organic' in data:
                for item in data['organic']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'position': item.get('position')
                    })

            self.logger.info(f"Found {len(results)} search results")
            return results

        except requests.RequestException as e:
            self.logger.error(f"Google search request failed: {str(e)}")
            raise CustomError(f"Google search failed: {str(e)}", 400)
        except Exception as e:
            self.logger.error(f"Error during Google search: {str(e)}")
            raise CustomError(f"Search processing failed: {str(e)}", 400)

    def _process_candidate(self, candidate: Candidate) -> None:
        """Process Google search data for a single candidate"""
        try:
            self.logger.info(f"Starting Google scraping for candidate ID: {candidate.id}")

            # Set initial processing status
            self.__candidate_service.set_pipeline_status_to_google_scrape(candidate.id)

            self.monitor.update_state(
                "google_scraping",
                PipelineStatus.RUNNING,
                message=f"Scraping Google data for candidate {candidate.id}"
            )

            parsed_data = candidate.parsed_resume_data
            if not parsed_data:
                self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
                raise CustomError("No parsed resume data found", 400)

            try:
                google_results = self._search_candidate(parsed_data)

                if google_results:
                    # Update parsed data with Google search results
                    parsed_data['google_results'] = google_results
                    candidate.parsed_resume_data = parsed_data
                    candidate.updated_at = datetime.utcnow()

                    db.session.commit()
                    self.logger.info(f"Successfully updated database for candidate: {candidate.id}")

                    # Move to next pipeline stage
                    self.__candidate_service.set_pipeline_status_to_linkedin_scrape(candidate.id)

                    self.monitor.update_state(
                        "google_scraping",
                        PipelineStatus.IDLE,
                        message=f"Successfully processed candidate {candidate.id}"
                    )
                else:
                    self.logger.warning(f"No Google results found for candidate {candidate.id}")
                    # Even with no results, move to next stage
                    self.__candidate_service.set_pipeline_status_to_linkedin_scrape(candidate.id)
                    candidate.updated_at = datetime.utcnow()
                    db.session.commit()

            except Exception as e:
                self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
                self.logger.error(f"Error processing Google search: {str(e)}")
                db.session.rollback()
                self.monitor.update_state(
                    "google_scraping",
                    PipelineStatus.ERROR,
                    message="Failed to process Google search",
                    error_message=str(e)
                )
                raise

        except Exception as e:
            self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
            self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
            db.session.rollback()
            self.monitor.update_state(
                "google_scraping",
                PipelineStatus.ERROR,
                message="Pipeline error",
                error_message=str(e)
            )
            raise CustomError(f"Error processing candidate: {str(e)}", 400)