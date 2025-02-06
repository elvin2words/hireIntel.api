from datetime import datetime
from typing import Optional, Dict, Any, List

from src.Helpers.ErrorHandling import CustomError
from src.Modules.Jobs.JobDTOs import (
    JobDTO,
    JobTechnicalSkillDTO,
    JobSoftSkillDTO,
    JobEducationDTO
)
from src.Modules.Jobs.JobModels import (
    Job,
    JobStatus,
    JobTechnicalSkill,
    JobSoftSkill,
    JobEducation,
    EmploymentType,
    ExperienceLevel
)
from src.Modules.Jobs.JobRepository import JobRepositoryFactory


class JobService:
    def __init__(self):
        factory = JobRepositoryFactory()
        self.__job_repository = factory.create_job_repository()
        self.__technical_skill_repository = factory.create_technical_skill_repository()
        self.__soft_skill_repository = factory.create_soft_skill_repository()
        self.__education_repository = factory.create_education_repository()

        # Initialize DTOs
        self.__job_dto = JobDTO()
        self.__technical_skill_dto = JobTechnicalSkillDTO()
        self.__soft_skill_dto = JobSoftSkillDTO()
        self.__education_dto = JobEducationDTO()

    def fetch_all(self, filters=None) -> List[Dict]:
        """
        Fetch all jobs with optional filters
        """
        try:
            jobs = self.__job_repository.get_all_jobs(filters)
            if not jobs:
                return []

            return self.__job_dto.dump(jobs, many=True)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))

    def fetch_by_id(self, job_id: str) -> Dict:
        """
        Fetch a job by ID with all related data
        """
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            # Get related data
            technical_skills = self.__technical_skill_repository.get_by_job_id(job_id)
            soft_skills = self.__soft_skill_repository.get_by_job_id(job_id)
            education_requirements = self.__education_repository.get_by_job_id(job_id)

            # Combine all data into job object before serialization
            setattr(job, 'technical_skills', technical_skills)
            setattr(job, 'soft_skills', soft_skills)
            setattr(job, 'education_requirements', education_requirements)

            return self.__job_dto.dump(job)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))

    def create_job(self, job_data: Dict[str, Any]) -> Dict:
        """
        Create a new job with all related data
        """
        try:
            # Convert string enums to proper enum values
            job_data['employment_type'] = EmploymentType(job_data['employment_type'])
            job_data['experience_level'] = ExperienceLevel(job_data['experience_level'])
            job_data['status'] = JobStatus.DRAFT

            # Convert application_deadline to datetime if provided
            if 'application_deadline' in job_data and job_data['application_deadline']:
                job_data['application_deadline'] = datetime.fromisoformat(
                    job_data['application_deadline'].replace('Z', '+00:00')
                )

            # Extract related data
            technical_skills_data = job_data.pop('technical_skills', [])
            soft_skills_data = job_data.pop('soft_skills', [])
            education_requirements_data = job_data.pop('education_requirements', [])

            # Create main job record
            job_fields = {k: v for k, v in job_data.items() if hasattr(Job, k)}
            job = Job(**job_fields)
            saved_job = self.__job_repository.create(job)

            # Add technical skills
            technical_skills = []
            for skill_data in technical_skills_data:
                skill = JobTechnicalSkill(job_id=saved_job.id, **skill_data)
                technical_skills.append(self.__technical_skill_repository.create(skill))

            # Add soft skills
            soft_skills = []
            for skill_data in soft_skills_data:
                skill = JobSoftSkill(job_id=saved_job.id, **skill_data)
                soft_skills.append(self.__soft_skill_repository.create(skill))

            # Add education requirements
            education_requirements = []
            for edu_data in education_requirements_data:
                education = JobEducation(job_id=saved_job.id, **edu_data)
                education_requirements.append(self.__education_repository.create(education))

            # Set related data for serialization
            setattr(saved_job, 'technical_skills', technical_skills)
            setattr(saved_job, 'soft_skills', soft_skills)
            setattr(saved_job, 'education_requirements', education_requirements)

            return self.__job_dto.dump(saved_job)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))

    def update_job(self, job_id: str, job_data: Dict[str, Any]) -> Dict:
        """
        Update a job and its related data
        """
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            # Handle enum conversions if present
            if 'employment_type' in job_data:
                job_data['employment_type'] = EmploymentType(job_data['employment_type'])
            if 'experience_level' in job_data:
                job_data['experience_level'] = ExperienceLevel(job_data['experience_level'])
            if 'status' in job_data:
                job_data['status'] = JobStatus(job_data['status'])

            # Convert application_deadline if present
            if 'application_deadline' in job_data and job_data['application_deadline']:
                job_data['application_deadline'] = datetime.fromisoformat(
                    job_data['application_deadline'].replace('Z', '+00:00')
                )

            # Extract related data
            technical_skills_data = job_data.pop('technical_skills', None)
            soft_skills_data = job_data.pop('soft_skills', None)
            education_requirements_data = job_data.pop('education_requirements', None)

            # Update main job fields
            for field, value in job_data.items():
                if hasattr(job, field):
                    setattr(job, field, value)

            job.updated_at = datetime.utcnow()
            updated_job = self.__job_repository.update(job)

            # Update technical skills if provided
            if technical_skills_data is not None:
                self.__technical_skill_repository.delete_by_job_id(job_id)
                technical_skills = []
                for skill_data in technical_skills_data:
                    skill = JobTechnicalSkill(job_id=job_id, **skill_data)
                    technical_skills.append(self.__technical_skill_repository.create(skill))
                setattr(updated_job, 'technical_skills', technical_skills)

            # Update soft skills if provided
            if soft_skills_data is not None:
                self.__soft_skill_repository.delete_by_job_id(job_id)
                soft_skills = []
                for skill_data in soft_skills_data:
                    skill = JobSoftSkill(job_id=job_id, **skill_data)
                    soft_skills.append(self.__soft_skill_repository.create(skill))
                setattr(updated_job, 'soft_skills', soft_skills)

            # Update education requirements if provided
            if education_requirements_data is not None:
                self.__education_repository.delete_by_job_id(job_id)
                education_requirements = []
                for edu_data in education_requirements_data:
                    education = JobEducation(job_id=job_id, **edu_data)
                    education_requirements.append(self.__education_repository.create(education))
                setattr(updated_job, 'education_requirements', education_requirements)

            return self.fetch_by_id(job_id)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))

    def delete_job(self, job_id: str) -> None:
        """
        Delete a job and all its related data
        """
        try:
            # Check if job exists
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            # Delete related data first
            self.__technical_skill_repository.delete_by_job_id(job_id)
            self.__soft_skill_repository.delete_by_job_id(job_id)
            self.__education_repository.delete_by_job_id(job_id)

            # Then delete the job
            self.__job_repository.delete(job)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))

    def publish_job(self, job_id: str) -> Dict:
        """
        Publish a job by changing its status to ACTIVE
        """
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            job.status = JobStatus.ACTIVE
            job.published_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()

            self.__job_repository.update(job)
            return self.fetch_by_id(job_id)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))

    def close_job(self, job_id: str) -> Dict:
        """
        Close a job by changing its status to CLOSED
        """
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            job.status = JobStatus.CLOSED
            job.updated_at = datetime.utcnow()

            self.__job_repository.update(job)
            return self.fetch_by_id(job_id)
        except Exception as e:
            raise CustomError(str(e), getattr(e, 'code', 400))