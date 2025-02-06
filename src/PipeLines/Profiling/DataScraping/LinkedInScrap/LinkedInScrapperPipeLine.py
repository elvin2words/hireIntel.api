from flask import Flask
from typing import List, Optional, Dict
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapServices import GoogleScrapDataService
from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapService import LinkedInScrapDataService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.DataScraping.LinkedInScrap.RapidLinkedInScrapper import RapidLinkedInAPIClient
from src.Helpers.ErrorHandling import CustomError


class LinkedInScrapingConfig(PipelineConfig):
    def __init__(self,
                 name: str = "linkedin_scraping",
                 batch_size: int = 10,
                 process_interval: int = 300,
                 linkedin_email: str = "",
                 linkedin_password: str = ""):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.linkedin_email = linkedin_email
        self.linkedin_password = linkedin_password


class LinkedInScrapingPipeline(BasePipeline):
    def __init__(self, app: Flask, config: LinkedInScrapingConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: LinkedInScrapingConfig = config
        self.__candidateService = CandidateService()
        self.__googleScrapDataService = GoogleScrapDataService()
        self.__linkedInScrapDataService = LinkedInScrapDataService()
        self.__rapidLinkedInScraper = RapidLinkedInAPIClient()

    def get_input_data(self) -> List[Candidate]:
        return (Candidate.query
                .filter_by(pipeline_status=CandidatePipelineStatus.LINKEDIN_SCRAPE)
                .limit(self.config.batch_size)
                .all())

    def process_item(self, candidate: Candidate) -> Optional[Dict]:
        handle_data = self.__googleScrapDataService.getLinkedInHandle(candidate.id)
        username = handle_data["handle"]

        if not username:
            raise CustomError(f"No LinkedIn URL found for candidate {candidate.id}", 400)

        profile_data = self.__rapidLinkedInScraper.get_profile(username)
        return {'candidate_id': candidate.id, 'profile_data': profile_data}

    def update_output(self, results: List[Dict]) -> None:
        for result in results:
            if result:
                self.__linkedInScrapDataService.save_profile(
                    result['candidate_id'],
                    result['profile_data']
                )
                self.__candidateService.set_pipeline_status_to_github_scrape(
                    result['candidate_id']
                )

    def handle_item_failure(self, candidate: Candidate, error: Exception) -> None:
        self.logger.error(f"LinkedIn scraping failed for candidate {candidate.id}: {str(error)}")
        self.__candidateService.set_pipeline_status_to_linkedin_scrape_failed(candidate.id)
# from Demos.win32ts_logoff_disconnected import username
# from flask import Flask
# from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
# from src.Modules.Candidate.CandidateService import CandidateService
# from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapServices import GoogleScrapDataService
# from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapService import LinkedInScrapDataService
# from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
# from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
# from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
# from src.Helpers.ErrorHandling import CustomError
#
# from src.PipeLines.Profiling.DataScraping.LinkedInScrap.RapidLinkedInScrapper import RapidLinkedInAPIClient
#
#
# class LinkedInScrapingConfig(PipelineConfig):
#     def __init__(self,
#                  name: str = "linkedin_scraping",
#                  batch_size: int = 10,
#                  process_interval: int = 300,
#                  linkedin_email: str = "",
#                  linkedin_password: str = ""):
#         super().__init__(name, batch_size, process_interval=process_interval)
#         self.linkedin_email = linkedin_email
#         self.linkedin_password = linkedin_password
#
#
# class LinkedInScrapingPipeline(BasePipeline):
#     def __init__(self, app: Flask, config: LinkedInScrapingConfig, monitor: PipelineMonitor):
#         super().__init__(app, config, monitor)
#         self.config: LinkedInScrapingConfig = config
#         self.__candidateService =  CandidateService()
#         self.__googleScrapDataService = GoogleScrapDataService()
#         self.__linkedInScrapDataService = LinkedInScrapDataService()
#         # self.__linkedInScrapper = LinkedInScraper(headless=True)
#         self.__rapidLinkedInScraper = RapidLinkedInAPIClient()
#
#
#     def process_batch(self):
#         """Process a batch of candidates for LinkedIn data scraping"""
#         try:
#             # Todo find proper way to handle github and linkedin failed, the pipeline should continue cause a user might not have a github or linkedin
#             # Find candidates that need LinkedIn scraping
#             candidates = (Candidate.query
#                           .filter_by(
#                             pipeline_status=CandidatePipelineStatus.LINKEDIN_SCRAPE
#                           )
#                           .limit(self.config.batch_size)
#                           .all())
#
#             if not candidates:
#                 self.logger.info("No candidates found for LinkedIn scraping")
#                 return
#
#             self.logger.info(f"Processing {len(candidates)} candidates for LinkedIn scraping")
#
#             for candidate in candidates:
#                 try:
#                     self._process_candidate(candidate)
#
#                 except Exception as e:
#                     self.logger.error(
#                         f"Failed to process LinkedIn data for candidate {candidate.id}: {str(e)}"
#                     )
#
#                     ## Update the pipeline status
#                     self.__candidateService.set_pipeline_status_to_linkedin_scrape_failed(candidate.id)
#
#         except Exception as e:
#             self.logger.error(f"Batch processing failed: {str(e)}")
#
#
#     def _process_candidate(self, candidate: Candidate) -> None:
#         """Process LinkedIn data for a single candidate"""
#         try:
#             self.logger.info(f"Starting LinkedIn scraping for candidate ID: {candidate.id}")
#
#             self.monitor.update_state(
#                 self.config.name,
#                 PipelineStatus.RUNNING,
#                 message=f"Scraping LinkedIn data for candidate {candidate.id}"
#             )
#
#             # social media handle / social media username (IN PUT)
#             candidateProfessionalHandle = self.__googleScrapDataService.getLinkedInHandle(candidate.id)
#             _username = candidateProfessionalHandle["handle"]
#             print("my username:", _username)
#
#             if not _username:
#                 self.logger.info(f"No LinkedIn URL found for candidate {candidate.id}")
#                 self.__candidateService.set_pipeline_status_to_linkedin_scrape_failed(candidate.id)
#                 return
#
#             profile_data = self.__rapidLinkedInScraper.get_profile(_username)
#
#             #Pass the json data and save it (OUT PUT)
#             self.__linkedInScrapDataService.save_profile(candidate.id, profile_data)
#             self.__candidateService.set_pipeline_status_to_github_scrape(candidate.id)
#
#             self.logger.info(f"Successfully updated LinkedIn data for candidate: {candidate.id}")
#
#         except Exception as e:
#             self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
#             self.__candidateService.set_pipeline_status_to_linkedin_scrape_failed(candidate.id)
#             raise CustomError(f"Error processing candidate: {str(e)}", 400)
#
#         # finally:
#         #     self.__linkedInScrapper.close()