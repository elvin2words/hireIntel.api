import json
from typing import Dict, Optional

from src.Helpers.LLMService import LLMService
from src.Modules.Jobs.JobService import JobService
from src.Modules.PipeLineData.GithubSrapData.GithubScrapServices import GitHubScrapDataService
from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapService import LinkedInScrapDataService
from src.Modules.PipeLineData.TextExtractionData.TextExtractionService import TextExtractionDataService


class ProfileCreationService:
    def __init__(self):
        self.__job_service = JobService()
        self.__resume_service = TextExtractionDataService()
        self.__linkedin_service = LinkedInScrapDataService()
        self.__github_service = GitHubScrapDataService()
        self.__llm_service = LLMService()

    def create_profile(self, candidate_id: str, job_id: str) -> Dict:
        # Fetch data
        job_data = self.__job_service.fetch_by_id(job_id)
        resume_data = self.__resume_service.get_resume_by_candidate_id(candidate_id)
        linkedin_data = self.__linkedin_service.get_profile_by_candidate_id(candidate_id)
        github_data = self.__github_service.get_profile_by_candidate_id(candidate_id)

        # print(f"LinkedIn unclean: {json.dumps(linkedin_data, indent=2)}")

        # Clean data
        cleaned_data = self.__prepare_data_for_comparison(
            job_data, resume_data, linkedin_data, github_data
        )

        # print(f"cleaned_data: {json.dumps(cleaned_data['linkedin'], indent=2)}")

        # Generate prompt and get profile analysis
        prompt = self.__generate_llm_prompt(cleaned_data)
        try:
            profile_analysis = self.__llm_service.create_profile(prompt)
            print("Candidate profile created", json.dumps(profile_analysis, indent=2))
            return profile_analysis
        except Exception as e:
            raise Exception(f"Failed to create profile: {str(e)}")

    def __prepare_data_for_comparison(self, job_data: Dict, resume_data: Dict,
                                      linkedin_data: Optional[Dict], github_data: Optional[Dict]) -> Dict:
        cleaned_data = {
            "job": self.__clean_job_data(job_data),
            "resume": self.__clean_resume_data(resume_data),
            "linkedin": self.__clean_linkedin_data(linkedin_data) if linkedin_data else None,
            "github": self.__clean_github_data(github_data) if github_data else None
        }
        return cleaned_data

    def __clean_job_data(self, job_data: Dict) -> Dict:
        return {
            "title": job_data.get("title"),
            "required_skills": job_data.get("required_skills", []),
            "preferred_skills": job_data.get("preferred_skills", []),
            "required_experience": job_data.get("required_experience"),
            "education_requirements": job_data.get("education_requirements"),
            "job_description": job_data.get("description")
        }

    def __clean_resume_data(self, resume_data: Dict) -> Dict:
        return {
            "education": [
                {
                    "institution": edu.get("institution"),
                    "degree": edu.get("degree"),
                    "field": edu.get("fieldOfStudy")
                }
                for edu in resume_data.get("education", [])
            ],
            "experience": [
                {
                    "company": exp.get("company"),
                    "position": exp.get("position"),
                    "start_date": exp.get("startDate"),
                    "end_date": exp.get("endDate"),
                    "description": exp.get("description")
                }
                for exp in resume_data.get("workExperience", [])
            ],
            "technical_skills": [
                {
                    "name": skill.get("skillName"),
                    "proficiency": skill.get("proficiencyLevel"),
                    "years": skill.get("yearsExperience")
                }
                for skill in resume_data.get("technicalSkills", [])
            ],
            "soft_skills": [skill.get("skillName") for skill in resume_data.get("softSkills", [])]
        }

    def __clean_linkedin_data(self, linkedin_data: Dict) -> Dict:
        return {
            "headline": linkedin_data.get("headline"),
            "summary": linkedin_data.get("summary"),
            "experience": [
                {
                    "company": exp.get("company"),
                    "title": exp.get("title"),
                    "duration": exp.get("duration"),
                    "description": exp.get("description")
                }
                for exp in linkedin_data.get("experience", [])
            ],
            "skills": linkedin_data.get("skills", [])
        }

    def __clean_github_data(self, github_data: Dict) -> Dict:
        return {
            "contributions": github_data.get("contributionsLastYear"),
            "total_stars": github_data.get("totalStarsEarned"),
            "public_repos": github_data.get("publicRepos"),
            "top_languages": self.__extract_top_languages(github_data.get("repositories", [])),
            "significant_projects": [
                {
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "stars": repo.get("stars", 0),
                    "language": repo.get("language")
                }
                for repo in github_data.get("repositories", [])
                if repo.get("stars", 0) > 0
            ]
        }


    def __extract_top_languages(self, repositories: list) -> Dict:
        language_usage = {}
        for repo in repositories:
            lang_breakdown = repo.get("languages_breakdown", {})
            for lang, percentage in lang_breakdown.items():
                language_usage[lang] = language_usage.get(lang, 0) + percentage
        return dict(sorted(language_usage.items(), key=lambda x: x[1], reverse=True)[:5])


    def __generate_llm_prompt(self, cleaned_data: Dict) -> str:
        json_structure = '''{
                              "overallMatch": {
                                "score": "number (0-100)",
                                "details": "string explaining match rationale"
                              },
                              "technicalSkills": {
                                "score": "number (0-100)",
                                "skillMatches": [
                                  {
                                    "skill": "string",
                                    "jobRelevance": "number (0-100)",
                                    "candidateProficiency": "number (0-100)"
                                  }
                                ],
                                "frameworksAndTools": [{"name": "string", "proficiency": "number"}]
                              },
                              "softSkills": {
                                "score": "number (0-100)",
                                "skillMatches": [{"skill": "string", "proficiency": "number"}]
                              },
                              "experience": {
                                "score": "number (0-100)",
                                "yearsOfExperience": "number",
                                "industryExperience": [{"industry": "string", "years": "number"}],
                                "relevantRoles": [{"title": "string", "company": "string", "duration": "number"}]
                              },
                              "education": {
                                "score": "number (0-100)",
                                "degrees": [{"degree": "string", "major": "string", "institution": "string"}]
                              },
                              "projectsAndAchievements": {
                                "score": "number (0-100)",
                                "items": [{"name": "string", "description": "string", "relevance": "number"}]
                              },
                              "socialPresence": {
                                "score": "number (0-100)",
                                "linkedInActivityScore": "number",
                                "githubContributionScore": "number",
                                "blogPostScore": "number"
                              },
                              "diversity": "boolean"
                            }
                        '''

        prompt = f"""Act as an expert technical recruiter analyzing candidate data against job requirements.
                Context:
                Job Requirements: {cleaned_data['job']}
                Resume Data: {cleaned_data['resume']}
                LinkedIn Data: {cleaned_data['linkedin']}
                GitHub Data: {cleaned_data['github']}
                
                Task: Generate a comprehensive candidate-job match analysis as a JSON object with the following structure:
                
                {json_structure}
                
                Analysis Guidelines:
                1. Base all scores on concrete evidence from provided data
                2. Focus on job requirement alignment
                3. Consider both direct and transferable skills
                4. Weight recent experience more heavily
                5. Factor in project complexity and impact
                6. Consider both quantity and quality of contributions
                7. Evaluate breadth and depth of technical expertise
                8. Consolidate identical or overlapping work experiences from resume, LinkedIn, and GitHub into single entries
                9. Merge matching education records from different sources rather than counting them multiple times
                
                Provide the analysis as a JSON object only, with no additional text.
                """
        return prompt