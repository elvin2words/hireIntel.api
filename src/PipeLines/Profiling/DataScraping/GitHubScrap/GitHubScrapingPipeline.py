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
        self.__candidateService.set_pipeline_status_to_github_scrape_failed(candidate.id)
        db.session.rollback()

# from flask import Flask
# from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
# from src.Modules.Candidate.CandidateService import CandidateService
# from src.Modules.PipeLineData.GithubSrapData.GithubScrapServices import GitHubScrapDataService
# from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapDTOs import CandidateProfessionalHandleDTO
# from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapServices import GoogleScrapDataService
# from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
# from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
# from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
# from src.PipeLines.Profiling.DataScraping.GitHubScrap.GithubScraper import GitHubScraper
# from src.config.DBModelsConfig import db
# from src.Helpers.ErrorHandling import CustomError
#
#
# class GitHubScrapingConfig(PipelineConfig):
#     def __init__(self,
#                  name: str = "github_scraping",
#                  batch_size: int = 10,
#                  process_interval: int = 300,
#                  github_token: str = ""):
#         super().__init__(name, batch_size, process_interval=process_interval)
#         self.github_token = github_token
#
#
# class GitHubScrapingPipeline(BasePipeline):
#     def __init__(self, app: Flask, config: GitHubScrapingConfig, monitor: PipelineMonitor):
#         super().__init__(app, config, monitor)
#         self.config: GitHubScrapingConfig = config
#         self.__githubScrapper = GitHubScraper(config.github_token)
#         self.__candidateService = CandidateService()
#         self.__googleScrapDataService = GoogleScrapDataService()
#         self.__githubScrapDataService = GitHubScrapDataService()
#
#     def process_batch(self):
#         """Process a batch of candidates for GitHub data scraping"""
#         try:
#             # Todo find proper way to handle github and linkedin failed, the pipeline should continue cause a user might not have a github or linkedin
#             # Find candidates that need GitHub scraping (IN PUT)
#             candidates = (Candidate.query
#                           .filter_by(
#                                 pipeline_status=CandidatePipelineStatus.GITHUB_SCRAPE
#                           )
#                           .limit(self.config.batch_size)
#                           .all())
#
#             if not candidates:
#                 self.logger.info("No candidates found for GitHub scraping")
#                 return
#
#             self.logger.info(f"Processing {len(candidates)} candidates for GitHub scraping")
#
#             for candidate in candidates:
#                 try:
#                     self._process_candidate(candidate)
#                 except Exception as e:
#                     self.logger.error(
#                         f"Failed to process GitHub data for candidate {candidate.id}: {str(e)}"
#                     )
#                     self.__candidateService.set_pipeline_status_to_github_scrape_failed(candidate.id)
#
#         except Exception as e:
#             self.logger.error(f"Batch processing failed: {str(e)}")
#             raise
#
#     def _process_candidate(self, candidate: Candidate) -> None:
#         """Process GitHub data for a single candidate with comprehensive status tracking"""
#         try:
#             self.logger.info(f"Starting GitHub scraping for candidate ID: {candidate.email}")
#
#             self.monitor.update_state(
#                 "github_scraping",
#                 PipelineStatus.RUNNING,
#                 message=f"Scraping GitHub data for candidate {candidate.id}"
#             )
#
#             # social media handle / social media username (IN PUT)
#             candidateGithubHandle = self.__googleScrapDataService.getGitHubHandle(candidate.id)
#             username = candidateGithubHandle["handle"]
#
#             if not candidateGithubHandle:
#                 self.__candidateService.set_pipeline_status_to_github_scrape_failed(candidate.id)
#                 self.logger.info(f"Failed to retrieve candidate {candidate.email} username")
#                 raise CustomError("Failed to retrieve candidate username", 400)
#
#             self.logger.info(f"Fetching GitHub data for username: {username}")
#
#             github_info = self.__githubScrapper.get_user_stats(username)
#
#             print(f"Successfully scraped GitHub data for candidate {candidate.id}: {github_info}")
#
#             # Save scrapped info in database (OUT PUT)
#             self.__githubScrapDataService.save_profile(candidate.id, github_info)
#             self.logger.info(f"Successfully updated database for candidate: {candidate.id}")
#
#             # Move to next pipeline stage
#             self.__candidateService.set_pipeline_status_to_profile_creation(candidate.id)
#
#             self.monitor.update_state(
#                 "github_scraping",
#                 PipelineStatus.IDLE,
#                 message=f"Successfully processed candidate {candidate.id}"
#             )
#
#         except Exception as e:
#             self.__candidateService.set_pipeline_status_to_github_scrape_failed(candidate.id)
#             self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
#             db.session.rollback()
#             self.monitor.update_state(
#                 "github_scraping",
#                 PipelineStatus.ERROR,
#                 message="Failed to fetch GitHub data",
#                 error_message=str(e)
#             )
#             raise CustomError(f"Error processing candidate: {str(e)}", 400)