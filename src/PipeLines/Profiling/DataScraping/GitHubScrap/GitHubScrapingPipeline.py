from flask import Flask
from typing import List, Optional, Dict
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.GithubSrapData.GithubScrapServices import GitHubScrapDataService
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapServices import GoogleScrapDataService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.DataScraping.GitHubScrap.GithubScraper import GitHubScraper
from src.config.DBModelsConfig import db
from src.Helpers.ErrorHandling import CustomError


class GitHubScrapingConfig(PipelineConfig):
    def __init__(self,
                 name: str = "github_scraping",
                 batch_size: int = 10,
                 process_interval: int = 300,
                 github_token: str = ""):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.github_token = github_token


class GitHubScrapingPipeline(BasePipeline):
    def __init__(self, app: Flask, config: GitHubScrapingConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: GitHubScrapingConfig = config
        self.__githubScrapper = GitHubScraper(config.github_token)
        self.__candidateService = CandidateService()
        self.__googleScrapDataService = GoogleScrapDataService()
        self.__githubScrapDataService = GitHubScrapDataService()

    def get_input_data(self) -> List[Candidate]:
        """Retrieve candidates needing GitHub scraping"""
        return (Candidate.query
                .filter_by(pipeline_status=CandidatePipelineStatus.GITHUB_SCRAPE)
                .limit(self.config.batch_size)
                .all())

    def process_item(self, candidate: Candidate) -> Optional[Dict]:
        """Process GitHub data for a single candidate"""
        candidateGithubHandle = self.__googleScrapDataService.getGitHubHandle(candidate.id)
        if not candidateGithubHandle:
            raise CustomError(f"No GitHub handle found for candidate {candidate.email}", 400)

        username = candidateGithubHandle["handle"]
        github_info = self.__githubScrapper.get_user_stats(username)

        if github_info is None:
            raise CustomError(f"Failed to fetch Github profile for :  {candidate.email}", 400)

        return {
            'candidate_id': candidate.id,
            'github_info': github_info
        }

    def update_output(self, results: List[Dict]) -> None:
        """Save GitHub data and update candidate status"""
        for result in results:
            if result:
                self.__githubScrapDataService.save_profile(
                    result['candidate_id'],
                    result['github_info']
                )
                self.__candidateService.set_pipeline_status_to_profile_creation(
                    result['candidate_id']
                )

    def handle_item_failure(self, candidate: Candidate, error: Exception) -> None:
        """Handle failures in GitHub data processing"""
        self.logger.error(f"GitHub scraping failed for candidate {candidate.id}: {str(error)}")
        """
            If it fails to retrieve it should continue 
            Considering most people wont have Github or they delete them 
            We will use the resume and other data we have to create a profile
        """
        self.__candidateService.set_pipeline_status_to_profile_creation(candidate.id)
        # self.__candidateService.set_pipeline_status_to_github_scrape_failed(candidate.id)
        db.session.rollback()