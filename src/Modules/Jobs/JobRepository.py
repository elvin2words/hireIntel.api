from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from src.Helpers.BaseRepository import BaseRepository
from src.Modules.Jobs.JobModels import (
    Job,
    JobTechnicalSkill,
    JobSoftSkill,
    JobEducation
)


class JobRepository(BaseRepository[Job]):
    def __init__(self):
        super().__init__(Job)

    def get_all_jobs(self, filters=None) -> List[Job]:
        """
        Get all jobs with optional filters
        """
        try:
            query = self._db.session.query(self._model)

            if filters:
                if 'status' in filters:
                    query = query.filter(Job.status == filters['status'])
                if 'experience_level' in filters:
                    query = query.filter(Job.experience_level == filters['experience_level'])
                if 'employment_type' in filters:
                    query = query.filter(Job.employment_type == filters['employment_type'])

            return query.all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """
        Get a job by its ID
        """
        return self.get_by_id(job_id)


class JobTechnicalSkillRepository(BaseRepository[JobTechnicalSkill]):
    def __init__(self):
        super().__init__(JobTechnicalSkill)

    def get_by_job_id(self, job_id: str) -> List[JobTechnicalSkill]:
        """
        Get all technical skills for a specific job
        """
        try:
            return self._db.session.query(JobTechnicalSkill).filter_by(job_id=job_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def delete_by_job_id(self, job_id: str) -> None:
        """
        Delete all technical skills for a specific job
        """
        try:
            self._db.session.query(JobTechnicalSkill).filter_by(job_id=job_id).delete()
            self._db.session.commit()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class JobSoftSkillRepository(BaseRepository[JobSoftSkill]):
    def __init__(self):
        super().__init__(JobSoftSkill)

    def get_by_job_id(self, job_id: str) -> List[JobSoftSkill]:
        """
        Get all soft skills for a specific job
        """
        try:
            return self._db.session.query(JobSoftSkill).filter_by(job_id=job_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def delete_by_job_id(self, job_id: str) -> None:
        """
        Delete all soft skills for a specific job
        """
        try:
            self._db.session.query(JobSoftSkill).filter_by(job_id=job_id).delete()
            self._db.session.commit()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class JobEducationRepository(BaseRepository[JobEducation]):
    def __init__(self):
        super().__init__(JobEducation)

    def get_by_job_id(self, job_id: str) -> List[JobEducation]:
        """
        Get all education requirements for a specific job
        """
        try:
            return self._db.session.query(JobEducation).filter_by(job_id=job_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def delete_by_job_id(self, job_id: str) -> None:
        """
        Delete all education requirements for a specific job
        """
        try:
            self._db.session.query(JobEducation).filter_by(job_id=job_id).delete()
            self._db.session.commit()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


# You might want to use a RepositoryFactory if you need to manage these repositories centrally
class JobRepositoryFactory:
    @staticmethod
    def create_job_repository() -> JobRepository:
        return JobRepository()

    @staticmethod
    def create_technical_skill_repository() -> JobTechnicalSkillRepository:
        return JobTechnicalSkillRepository()

    @staticmethod
    def create_soft_skill_repository() -> JobSoftSkillRepository:
        return JobSoftSkillRepository()

    @staticmethod
    def create_education_repository() -> JobEducationRepository:
        return JobEducationRepository()