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
                 serperToken: str = "",
                 githubToken: str = "",
                 rapid_api_key: str = "",
                 serperBaseUrl: str = "https://google.serper.dev/search"):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.serperToken = serperToken
        self.githubToken = githubToken
        self.rapid_api_key = rapid_api_key
        self.serperBaseUrl = serperBaseUrl


class GoogleScrapingPipeline(BasePipeline):
    def __init__(self, app: Flask, config: GoogleScrapingConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: GoogleScrapingConfig = config
        self.__scraper = ProfileScraper(config.githubToken,
                                        config.serperToken,
                                        config.serperBaseUrl,
                                        config.rapid_api_key)
        self.__candidate_service = CandidateService()
        self.__googleScrapDataService = GoogleScrapDataService()

    def get_input_data(self) -> List[Candidate]:
        return (Candidate.query
                .filter_by(pipeline_status=CandidatePipelineStatus.GOOGLE_SCRAPE)
                .limit(self.config.batch_size)
                .all())

    def process_item(self, candidate: Candidate) -> Optional[Dict]:
        profile: Profile = self.__scraper.find_profiles(candidate)

        if profile.githubHandle.github_username is None and profile.githubHandle.github_username is not None:
            raise CustomError(f"Failed to find user linkedin and github handles ", 400)

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
        """
            If it fails to retrieve the handles it should continue 
            Considering most people wont have linkedin or github handles
            We will use the resume and other data we have to create a profile
        """
        # since we failed to get linked in and GitHub handle we skip the scraping for LinkedIn and GitHub
        self.__candidate_service.set_pipeline_status_to_profile_creation(candidate.id)
        # self.__candidate_service.set_pipeline_status_to_google_scrape_failed(candidate.id)
        db.session.rollback()
