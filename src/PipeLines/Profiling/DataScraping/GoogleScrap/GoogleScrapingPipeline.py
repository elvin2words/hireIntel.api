from flask import Flask
from typing import List, Optional, Dict
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapServices import GoogleScrapDataService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.DataScraping.GoogleScrap.SerperGoogleScraper import ProfileScraper, Profile
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
        self.__scraper = ProfileScraper()
        self.__candidate_service = CandidateService()
        self.__googleScrapDataService = GoogleScrapDataService()

    def get_input_data(self) -> List[Candidate]:
        return (Candidate.query
                .filter_by(pipeline_status=CandidatePipelineStatus.GOOGLE_SCRAPE)
                .limit(self.config.batch_size)
                .all())

    def process_item(self, candidate: Candidate) -> Optional[Dict]:
        profile: Profile = self.__scraper.find_profiles(candidate)
        return {'candidate_id': candidate.id, 'profile': profile} if profile else None

    def update_output(self, results: List[Dict]) -> None:
        for result in results:
            if result:
                self.__googleScrapDataService.saveCandidateHandles(
                    result['candidate_id'],
                    result['profile']
                )
            self.__candidate_service.set_pipeline_status_to_linkedin_scrape(
                result['candidate_id']
            )

    def handle_item_failure(self, candidate: Candidate, error: Exception) -> None:
        self.logger.error(f"Google scraping failed for candidate {candidate.id}: {str(error)}")
        self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
        db.session.rollback()

# from flask import Flask
# from datetime import datetime
# from typing import Dict, Any, List, Optional
# import json
# import requests
# from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
# from src.Modules.Candidate.CandidateService import CandidateService
# from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapServices import GoogleScrapDataService
# from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
# from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
# from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
# from src.PipeLines.Profiling.DataScraping.GoogleScrap.SerperGoogleScraper import ProfileScraper, Profile
# from src.config.DBModelsConfig import db
# from src.Helpers.ErrorHandling import CustomError
#
#
# class GoogleScrapingConfig(PipelineConfig):
#     def __init__(self,
#                  name: str = "google_scraping",
#                  batch_size: int = 10,
#                  process_interval: int = 300,
#                  api_key: str = "",
#                  google_url: str = "https://google.serper.dev/search"):
#         super().__init__(name, batch_size, process_interval=process_interval)
#         self.api_key = api_key
#         self.google_url = google_url
#
#
# class GoogleScrapingPipeline(BasePipeline):
#     def __init__(self, app: Flask, config: GoogleScrapingConfig, monitor: PipelineMonitor):
#         super().__init__(app, config, monitor)
#         self.config: GoogleScrapingConfig = config
#         self.__scraper = ProfileScraper()
#         self.__candidate_service = CandidateService()
#         self.__googleScrapDataService = GoogleScrapDataService()
#
#     def process_batch(self):
#         """Process a batch of candidates for Google scraping"""
#         try:
#             # Find candidates that need Google scraping (IN PUT)
#             candidates = (Candidate.query
#                           .filter_by(pipeline_status=CandidatePipelineStatus.GOOGLE_SCRAPE)
#                           .limit(self.config.batch_size)
#                           .all())
#
#             if not candidates:
#                 self.logger.info("No candidates found for Google scraping")
#                 return
#
#             self.logger.info(f"Processing {len(candidates)} candidates for Google scraping")
#
#             for candidate in candidates:
#                 try:
#                     print(f"Processing candidate {candidate.id}")
#                     self._process_candidate(candidate)
#                 except Exception as e:
#                     self.logger.error(
#                         f"Failed to process Google data for candidate {candidate.id}: {str(e)}"
#                     )
#                     self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
#
#         except Exception as e:
#             self.logger.error(f"Batch processing failed: {str(e)}")
#             raise
#
#     def _process_candidate(self, candidate: Candidate) -> None:
#         """Process Google search data for a single candidate"""
#         try:
#             self.logger.info(f"Starting Google scraping for candidate ID: {candidate.id}")
#             self.monitor.update_state(
#                 "google_scraping",
#                 PipelineStatus.RUNNING,
#                 message=f"Scraping Google data for candidate {candidate.id}"
#             )
#
#             full_name = candidate.first_name + " " + candidate.last_name
#             profile: Profile = self.__scraper.find_profiles(candidate)
#
#             if profile:
#                 self.__googleScrapDataService.saveCandidateHandles(candidate.id, profile)
#                 self.__candidate_service.set_pipeline_status_to_linkedin_scrape(candidate.id)
#
#                 self.monitor.update_state(
#                     "google_scraping",
#                     PipelineStatus.IDLE,
#                     message=f"Successfully processed candidate {candidate.id}"
#                 )
#             else:
#                 self.logger.warning(f"Failed to find linkedIn and github handles for candidate {candidate.id}")
#                 self.__candidate_service.set_pipeline_status_to_linkedin_scrape(candidate.id)
#
#         except Exception as e:
#             self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
#             self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
#             db.session.rollback()
#             self.monitor.update_state(
#                 "google_scraping",
#                 PipelineStatus.ERROR,
#                 message=f"Pipeline error for candidate {candidate.id}",
#                 error_message=str(e)
#             )
#             raise CustomError(f"Error processing candidate {candidate.id}: {str(e)}", 400)