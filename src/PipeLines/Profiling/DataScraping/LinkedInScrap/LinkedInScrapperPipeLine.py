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
                 rapid_api_key: str = ""):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.rapid_api_key = rapid_api_key


class LinkedInScrapingPipeline(BasePipeline):
    def __init__(self, app: Flask, config: LinkedInScrapingConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: LinkedInScrapingConfig = config
        self.__candidateService = CandidateService()
        self.__googleScrapDataService = GoogleScrapDataService()
        self.__linkedInScrapDataService = LinkedInScrapDataService()
        self.__rapidLinkedInScraper = RapidLinkedInAPIClient(config.rapid_api_key)

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

        if profile_data is None:
            raise CustomError(f"Failed to get LinkedIn profile ", 400)

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
        """
            If it fails to retrieve it should continue 
            Considering most people wont have linkedin or they delete them 
            We will use the resume and other data we have to create a profile
        """
        self.__candidateService.set_pipeline_status_to_github_scrape(candidate.id)
        # self.__candidateService.set_pipeline_status_to_linkedin_scrape_failed(candidate.id)