from datetime import datetime
from typing import Dict, Any, List
import json
import requests

from src.config.DBModelsConfig import db
from src.Modules.Candidate.CandidateModels import Candidate
from src.Helpers.ErrorHandling import CustomError


class GoogleScrapingPipeline:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.google_url = "https://google.serper.dev/search"
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

    def search_candidate(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform Google search for candidate information"""
        try:
            # Extract search terms from parsed data
            personal_info = parsed_data.get('personal_information', {})
            name = personal_info.get('full_name', '')
            company = None

            # Get most recent company if available
            work_experience = parsed_data.get('work_experience', [])
            if work_experience:
                company = work_experience[0].get('company', '')

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

            # Execute search
            payload = json.dumps({"q": keyword})
            response = requests.post(self.google_url, headers=self.headers, data=payload)
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

            return results

        except requests.RequestException as e:
            raise CustomError(f"Google search failed: {str(e)}", 400)

    def run_pipeline(self):
        """Execute Google scraping pipeline"""
        try:
            # Get all candidates ready for Google scraping
            candidates = Candidate.query.filter_by(profiler_status='GOOGLE_SCRAP').all()

            for candidate in candidates:
                try:
                    parsed_data = candidate.parsed_resume_data
                    google_results = self.search_candidate(parsed_data)

                    if google_results:
                        # Update parsed data with Google search results
                        parsed_data['google_results'] = google_results
                        candidate.parsed_resume_data = parsed_data
                        candidate.profiler_status = 'PROFILE'
                        candidate.updated_at = datetime.utcnow()

                        db.session.commit()

                except Exception as e:
                    db.session.rollback()
                    print(f"Failed to process Google data for candidate {candidate.id}: {str(e)}")
                    continue

        except Exception as e:
            raise CustomError(f"Google pipeline execution failed: {str(e)}", 400)