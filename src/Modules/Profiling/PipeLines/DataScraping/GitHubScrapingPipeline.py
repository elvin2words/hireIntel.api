from datetime import datetime
from typing import Dict, Any

from src.Modules.Profiling.PipeLines.DataScraping.GithubScrapper import GitHubDataFetcher
from src.config.DBModelsConfig import db
from src.Modules.Candidate.CandidateModels import Candidate
from src.Helpers.ErrorHandling import CustomError


class GitHubScrapingPipeline:
    def __init__(self, github_token: str):
        self.github_token = github_token

    def scrape_github_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape GitHub data using GitHubDataFetcher"""
        fetcher = GitHubDataFetcher(self.github_token)

        github_info = parsed_data.get('personal_information', {}).get('github', {})
        if not github_info.get('username'):
            return None

        return fetcher.get_user_stats(github_info['username'])

    def run_pipeline(self):
        """Execute GitHub scraping pipeline"""
        try:
            # Get all candidates ready for GitHub scraping
            candidates = Candidate.query.filter_by(profiler_status='SCRAP').all()

            for candidate in candidates:
                try:
                    parsed_data = candidate.parsed_resume_data
                    github_data = self.scrape_github_data(parsed_data)

                    if github_data:
                        # Update parsed data with GitHub information
                        parsed_data['github_profile'] = github_data
                        candidate.parsed_resume_data = parsed_data
                        candidate.profiler_status = 'GOOGLE_SCRAP'
                        candidate.updated_at = datetime.utcnow()

                        db.session.commit()

                except Exception as e:
                    db.session.rollback()
                    print(f"Failed to process GitHub data for candidate {candidate.id}: {str(e)}")
                    continue

        except Exception as e:
            raise CustomError(f"GitHub pipeline execution failed: {str(e)}", 400)