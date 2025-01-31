from datetime import datetime
from typing import Dict, Any, List
from flask import Flask

from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.config.DBModelsConfig import db
from src.Modules.Candidate.CandidateModels import Candidate, CandidateStatus, CandidatePipelineStatus
from src.Modules.Jobs.JobModels import Job
from src.Helpers.ErrorHandling import CustomError


class ProfileCreationConfig(PipelineConfig):
    def __init__(self,
                 name: str = "profile_creation",
                 batch_size: int = 10,
                 process_interval: int = 300,  # 5 minutes
                 technical_weight: float = 0.4,
                 experience_weight: float = 0.35,
                 github_weight: float = 0.25,
                 min_passing_score: float = 70.0):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.technical_weight = technical_weight
        self.experience_weight = experience_weight
        self.github_weight = github_weight
        self.min_passing_score = min_passing_score


class ProfileCreationPipeline(BasePipeline):
    def __init__(self, app: Flask, config: ProfileCreationConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: ProfileCreationConfig = config

    def calculate_technical_score(self, candidate_skills: List[str], job: Job) -> float:
        """Calculate technical skills match score"""
        required_skills = [skill.skill_name for skill in job.technical_skills if skill.is_required]
        if not required_skills:
            return 0.0

        candidate_skill_set = set(candidate_skills)
        required_skill_set = set(required_skills)

        match_score = len(candidate_skill_set.intersection(required_skill_set)) / len(required_skill_set)
        return round(match_score * 100, 2)

    def calculate_experience_score(self, years_experience: int, job: Job) -> float:
        """Calculate experience score based on job requirements"""
        if years_experience >= job.min_experience_years:
            if job.max_experience_years and years_experience <= job.max_experience_years:
                return 100.0
            elif not job.max_experience_years:
                return 100.0
            else:
                over_experience = years_experience - job.max_experience_years
                return max(70.0 - (over_experience * 5), 0)

        return round((years_experience / job.min_experience_years) * 100, 2)

    def calculate_github_score(self, github_data: Dict[str, Any]) -> float:
        """Calculate GitHub activity score"""
        if not github_data:
            return 0.0

        grade_map = {
            'A+': 100, 'A': 95, 'A-': 90,
            'B+': 85, 'B': 80, 'B-': 75,
            'C+': 70, 'C': 65, 'C-': 60
        }

        return float(grade_map.get(github_data['user_info']['rating'], 60))

    def create_profile(self, candidate: Candidate) -> Dict[str, Any]:
        """Create comprehensive candidate profile"""
        try:
            parsed_data = candidate.parsed_resume_data
            job = candidate.job

            # Extract skills from parsed resume
            skills = (
                    parsed_data.get('skills', {}).get('programming_languages', []) +
                    parsed_data.get('skills', {}).get('frameworks_libraries', [])
            )

            technical_score = self.calculate_technical_score(skills, job)
            experience_score = self.calculate_experience_score(candidate.years_of_experience or 0, job)
            github_score = self.calculate_github_score(parsed_data.get('github_profile'))

            # Calculate overall score using weights from config
            overall_score = (
                    technical_score * self.config.technical_weight +
                    experience_score * self.config.experience_weight +
                    github_score * self.config.github_weight
            )

            profile = {
                'candidate_id': candidate.id,
                'job_id': job.id,
                'scores': {
                    'technical_score': technical_score,
                    'experience_score': experience_score,
                    'github_score': github_score,
                    'overall_score': round(overall_score, 2)
                },
                'skill_analysis': {
                    'matched_skills': list(set(skills).intersection(
                        skill.skill_name for skill in job.technical_skills
                    )),
                    'missing_skills': list(set(
                        skill.skill_name for skill in job.technical_skills
                    ) - set(skills))
                },
                'github_activity': parsed_data.get('github_profile', {}).get('user_info', {}),
                'online_presence': parsed_data.get('google_results', [])
            }

            return profile

        except Exception as e:
            self.logger.error(f"Error creating profile for candidate {candidate.id}: {str(e)}")
            raise CustomError(f"Error creating profile: {str(e)}", 400)

    def process_batch(self) -> None:
        """Process a batch of candidates for profile creation"""
        try:
            # Get candidates ready for profile creation
            candidates = Candidate.query.filter_by(
                pipeline_status=CandidatePipelineStatus.PROFILE_CREATION
            ).limit(self.config.batch_size).all()

            if not candidates:
                self.logger.info("No candidates found for profile creation")
                return

            self.logger.info(f"Processing {len(candidates)} candidates for profile creation")

            for candidate in candidates:
                try:
                    profile = self.create_profile(candidate)

                    # Update candidate with profile data
                    parsed_data = candidate.parsed_resume_data
                    parsed_data['profile'] = profile

                    candidate.parsed_resume_data = parsed_data
                    candidate.pipeline_status = CandidatePipelineStatus.PROFILE_CREATED
                    candidate.updated_at = datetime.utcnow()

                    # Update candidate status based on profile score
                    if profile['scores']['overall_score'] >= self.config.min_passing_score:
                        candidate.status = CandidateStatus.SCREENING

                    db.session.commit()
                    self.logger.info(f"Successfully created profile for candidate {candidate.id}")

                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"Failed to create profile for candidate {candidate.id}: {str(e)}")
                    self.monitor.update_state(
                        self.config.name,
                        PipelineStatus.ERROR,
                        error_message=f"Failed to create profile for candidate {candidate.id}: {str(e)}"
                    )
                    continue

        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            raise CustomError(f"Profile creation pipeline failed: {str(e)}", 400)

