from datetime import datetime
import uuid

from src.Helpers.ErrorHandling import CustomError
from src.Modules.Jobs.JobDTOs import JobDTO
from src.Modules.Jobs.JobModels import Job, JobStatus, JobTechnicalSkill, JobSoftSkill, JobEducation
from src.Modules.Jobs.JobRepository import JobRepository


class JobService:
    def __init__(self):
        self.__job_repository = JobRepository()

    def fetch_all(self, filters=None):
        try:
            jobs = self.__job_repository.get_all_jobs(filters)
            if len(jobs) == 0:
                raise Exception("No jobs found")
            return JobDTO(many=True).dump(jobs)
        except Exception as e:
            raise CustomError(str(e), 400)

    def fetch_by_id(self, job_id):
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)
            return JobDTO(many=False).dump(job)
        except Exception as e:
            raise CustomError(str(e), 400)

    def create_job(self, job_data):
        try:
            job = Job(
                id=str(uuid.uuid4()),
                title=job_data['title'],
                description=job_data['description'],
                company_id=job_data['company_id'],
                department=job_data.get('department'),
                location=job_data['location'],
                remote_policy=job_data.get('remote_policy'),
                employment_type=job_data['employment_type'],
                experience_level=job_data['experience_level'],
                min_experience_years=job_data['min_experience_years'],
                max_experience_years=job_data.get('max_experience_years'),
                min_salary=job_data.get('min_salary'),
                max_salary=job_data.get('max_salary'),
                currency=job_data.get('currency'),
                candidates_needed=job_data['candidates_needed'],
                status=JobStatus.DRAFT,
                application_deadline=job_data.get('application_deadline')
            )

            # Save the job first to get the ID
            self.__job_repository.save_job(job)

            # Add technical skills
            for skill_data in job_data.get('technical_skills', []):
                skill = JobTechnicalSkill(
                    job_id=job.id,
                    skill_name=skill_data['skill_name'],
                    years_experience=skill_data.get('years_experience'),
                    is_required=skill_data.get('is_required', True)
                )
                self.__job_repository.save_technical_skill(skill)

            # Add soft skills
            for skill_data in job_data.get('soft_skills', []):
                skill = JobSoftSkill(
                    job_id=job.id,
                    skill_name=skill_data['skill_name']
                )
                self.__job_repository.save_soft_skill(skill)

            # Add education requirements
            for edu_data in job_data.get('education_requirements', []):
                education = JobEducation(
                    job_id=job.id,
                    degree_level=edu_data['degree_level'],
                    field_of_study=edu_data['field_of_study'],
                    is_required=edu_data.get('is_required', True)
                )
                self.__job_repository.save_education_requirement(education)

            return JobDTO(many=False).dump(job)
        except Exception as e:
            raise CustomError(str(e), 400)

    def update_job(self, job_id, job_data):
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            # Define fields that can be updated
            updatable_fields = {
                'title', 'description', 'department', 'location',
                'remote_policy', 'employment_type', 'experience_level',
                'min_experience_years', 'max_experience_years',
                'min_salary', 'max_salary', 'currency',
                'candidates_needed', 'status', 'application_deadline'
            }

            # Only update fields that are provided in job_data
            for field in job_data:
                if field in updatable_fields:
                    setattr(job, field, job_data[field])

            # Update the timestamp
            job.updated_at = datetime.utcnow()

            # Save changes
            self.__job_repository.update_job(job)

            return JobDTO(many=False).dump(job)

        except Exception as e:
            raise CustomError(str(e), 400)

    def delete_job(self, job_id):
        try:
            self.__job_repository.delete_job(job_id)
        except Exception as e:
            raise CustomError(str(e), 400)

    def publish_job(self, job_id):
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            job.status = JobStatus.ACTIVE
            job.published_at = datetime.utcnow()

            self.__job_repository.update_job(job)
            return JobDTO(many=False).dump(job)
        except Exception as e:
            raise CustomError(str(e), 400)

    def close_job(self, job_id):
        try:
            job = self.__job_repository.get_job_by_id(job_id)
            if not job:
                raise CustomError("Job not found", 404)

            job.status = JobStatus.CLOSED
            self.__job_repository.update_job(job)
            return JobDTO(many=False).dump(job)
        except Exception as e:
            raise CustomError(str(e), 400)