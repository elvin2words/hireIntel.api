# src/Modules/Profiling/PipeLines/CreateProfile/ProfileCreationPipeline.py
from datetime import datetime
from typing import Dict, Any, List
from src.config.DBModelsConfig import db
from src.Modules.Candidate.CandidateModels import Candidate, CandidateStatus
from src.Modules.Jobs.JobModels import Job
from src.Helpers.ErrorHandling import CustomError
from src.Helpers.PipelineMonitor import PipelineStatus

class MonitoredProfileCreationPipeline:
    def __init__(self, monitor):
        self.monitor = monitor

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
            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.RUNNING,
                f"Creating profile for candidate {candidate.id}"
            )

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

            # Calculate overall score with weights
            weights = {
                'technical': 0.4,
                'experience': 0.35,
                'github': 0.25
            }

            overall_score = (
                technical_score * weights['technical'] +
                experience_score * weights['experience'] +
                github_score * weights['github']
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

            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.IDLE,
                f"Successfully created profile for candidate {candidate.id}",
                details={'scores': profile['scores']}
            )

            return profile

        except Exception as e:
            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.ERROR,
                error_message=f"Error creating profile: {str(e)}"
            )
            raise CustomError(f"Error creating profile: {str(e)}", 400)

    def run_pipeline(self):
        """Execute profile creation pipeline"""
        try:
            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.RUNNING,
                "Starting profile creation pipeline"
            )

            # Get all candidates ready for profile creation
            candidates = Candidate.query.filter_by(profiler_status='PROFILE').all()

            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.RUNNING,
                f"Found {len(candidates)} candidates to process"
            )

            for candidate in candidates:
                try:
                    profile = self.create_profile(candidate)

                    # Update candidate with profile data
                    parsed_data = candidate.parsed_resume_data
                    parsed_data['profile'] = profile

                    candidate.parsed_resume_data = parsed_data
                    candidate.profiler_status = 'COMPLETED'
                    candidate.updated_at = datetime.utcnow()

                    # Update candidate status based on profile score
                    if profile['scores']['overall_score'] >= 70:
                        candidate.status = CandidateStatus.SCREENING

                    db.session.commit()

                except Exception as e:
                    db.session.rollback()
                    self.monitor.update_pipeline_state(
                        "profile_creation",
                        PipelineStatus.ERROR,
                        error_message=f"Failed to create profile for candidate {candidate.id}: {str(e)}"
                    )
                    continue

            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.IDLE,
                "Profile creation pipeline completed"
            )

        except Exception as e:
            self.monitor.update_pipeline_state(
                "profile_creation",
                PipelineStatus.ERROR,
                error_message=f"Profile creation pipeline failed: {str(e)}"
            )
            raise CustomError(f"Profile creation pipeline failed: {str(e)}", 400)