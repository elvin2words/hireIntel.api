from flask import Flask
from datetime import datetime
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Modules.Candidate.CandidateService import CandidateService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.DataScraping.GitHubScrap.GithubScrapper import GitHubDataFetcher
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
        self.__github_fetcher = GitHubDataFetcher(config.github_token)
        self.__candidate_service = CandidateService()

    def process_batch(self):
        """Process a batch of candidates for GitHub data scraping"""
        try:
            # Find candidates that need GitHub scraping
            candidates = (Candidate.query
                          .filter_by(pipeline_status=CandidatePipelineStatus.GITHUB_SCRAPE)
                          .limit(self.config.batch_size)
                          .all())

            if not candidates:
                self.logger.info("No candidates found for GitHub scraping")
                return

            self.logger.info(f"Processing {len(candidates)} candidates for GitHub scraping")

            for candidate in candidates:
                try:
                    self._process_candidate(candidate)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process GitHub data for candidate {candidate.id}: {str(e)}"
                    )
                    self.__candidate_service.set_pipeline_status_to_github_scrape_failed(candidate.id)

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise

    def _process_candidate(self, candidate: Candidate) -> None:
        """Process GitHub data for a single candidate with comprehensive status tracking"""
        try:
            self.logger.info(f"Starting GitHub scraping for candidate ID: {candidate.id}")

            # Set initial processing status
            self.__candidate_service.set_pipeline_status_to_github_scrape(candidate.id)

            self.monitor.update_state(
                "github_scraping",
                PipelineStatus.RUNNING,
                message=f"Scraping GitHub data for candidate {candidate.id}"
            )

            parsed_data = candidate.parsed_resume_data
            if not parsed_data:
                self.__candidate_service.set_pipeline_status_to_github_scrape_failed(candidate.id)
                raise CustomError("No parsed resume data found", 400)

            github_info = parsed_data.get('personal_information', {}).get('github', {})

            if not github_info.get('username'):
                self.logger.info(f"No GitHub username found for candidate {candidate.id}")
                # Skip to next stage if no GitHub username found
                self.__candidate_service.set_pipeline_status_to_profile_creation(candidate.id)
                candidate.updated_at = datetime.utcnow()
                db.session.commit()
                return

            try:
                # Fetch GitHub data
                github_username = github_info['username']
                self.logger.info(f"Fetching GitHub data for username: {github_username}")

                github_data = self.__github_fetcher.get_user_stats(github_username)
                self.logger.info(f"Successfully retrieved GitHub data for username: {github_username}")

                # Update candidate data
                parsed_data['github_profile'] = github_data
                candidate.parsed_resume_data = parsed_data
                candidate.updated_at = datetime.utcnow()

                db.session.commit()
                self.logger.info(f"Successfully updated database for candidate: {candidate.id}")

                # Move to next pipeline stage
                self.__candidate_service.set_pipeline_status_to_profile_creation(candidate.id)

                self.monitor.update_state(
                    "github_scraping",
                    PipelineStatus.IDLE,
                    message=f"Successfully processed candidate {candidate.id}"
                )

            except Exception as e:
                self.__candidate_service.set_pipeline_status_to_github_scrape_failed(candidate.id)
                self.logger.error(f"Error fetching GitHub data: {str(e)}")
                db.session.rollback()
                self.monitor.update_state(
                    "github_scraping",
                    PipelineStatus.ERROR,
                    message="Failed to fetch GitHub data",
                    error_message=str(e)
                )
                raise

        except Exception as e:
            self.__candidate_service.set_pipeline_status_to_github_scrape_failed(candidate.id)
            self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
            db.session.rollback()
            self.monitor.update_state(
                "github_scraping",
                PipelineStatus.ERROR,
                message="Pipeline error",
                error_message=str(e)
            )
            raise CustomError(f"Error processing candidate: {str(e)}", 400)