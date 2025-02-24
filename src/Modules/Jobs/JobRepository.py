from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from src.Helpers.BaseRepository import BaseRepository
from src.Modules.Jobs.JobModels import (
    Job,
    JobTechnicalSkill,
    JobSoftSkill,
    JobEducation
)
import logging

# Set up logging for error handling
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def log_and_raise(e: Exception):
    #Log the exception and raise it
    logger.error(f"Database error: {str(e)}")
    raise e


# Common Methods Mixin for the Repositories
class JobDetailRepositoryMixin:
    def get_by_job_id(self, job_id:str) -> List:
        # Get all related items for a specific job
        try: 
            return self._db.session.query(self._model).filter_by(job_id=job_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def delete_by_job_id(self, job_id:str) -> None:
        # Delete all related items for a specific job
        try: 
            self._db.session.query(self._model).filter_by(job_id=job_id).delete()
            self._db.session.commit()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e        
        

# Extending the BaseRepository
class JobRepository(BaseRepository[Job]): 
    def __init__(self):
        super().__init__(Job) #PassJob model to the base repo.

    def get_all_jobs(self, filters=None) -> List[Job]:
        """
        Get all jobs with optional filters for status, experience_level and employment_type
        """
        try:
            query = self._db.session.query(self._model)

            # if filters:
            #     if 'status' in filters:
            #         query = query.filter(Job.status == filters['status'])
            #     if 'experience_level' in filters:
            #         query = query.filter(Job.experience_level == filters['experience_level'])
            #     if 'employment_type' in filters:
            #         query = query.filter(Job.employment_type == filters['employment_type'])

            # Dynamic Fitering function for any filter
            if filters:
                for key, value in filters.items():
                    if hasattr(Job, key):
                        query = query.filter(getattr(Job, key)==value)  
                                     
            return query.all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            log_and_raise(e)

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """
        Get a job by its ID.
        Inherited from BaseRepo.
        """
        return self.get_by_id(job_id)
    
    def search_jobs(self, query_str: str) -> List[Job]:
        # Search jobs by title or description using a keyword
        try:
            return(self._db.session.query(self._model).filter(Job.title.ilike(f"%{query_str}%"))
                   |(Job.description.ilike(f"%{query_str}%"))).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            log_and_raise(e)

    # def get_paginated_jobs(self, page: int, page)
    def get_paginated_jobs(self, page: int, page_size: int, filters=None) -> List[Job]: 
        """ Get paginated jobs with optional filters """ 
        try: 
            query = self._db.session.query(self._model) 
            if filters: 
                for key, value in filters.items(): 
                    if hasattr(Job, key): 
                        query = query.filter(getattr(Job, key) == value) 
            return query.offset((page - 1) * page_size).limit(page_size).all() 
        except SQLAlchemyError as e: 
            self._db.session.rollback() 
            log_and_raise(e) 
            
    def get_jobs_by_date_range(self, start_date, end_date) -> List[Job]: 
        """ Get jobs posted within a date range """ 
        try: 
            return self._db.session.query(self._model).filter( Job.posted_at.between(start_date, end_date)).all() 
        except SQLAlchemyError as e: 
            self._db.session.rollback() 
            log_and_raise(e) 


class JobTechnicalSkillRepository(BaseRepository[JobTechnicalSkill], JobDetailRepositoryMixin):
    def __init__(self):
        super().__init__(JobTechnicalSkill)

    # def get_by_job_id(self, job_id: str) -> List[JobTechnicalSkill]:
    #     """
    #     Get all associated technical skills for a specific job
    #     """
    #     try:
    #         return self._db.session.query(JobTechnicalSkill).filter_by(job_id=job_id).all()
    #     except SQLAlchemyError as e:
    #         self._db.session.rollback()
    #         raise e

    # def delete_by_job_id(self, job_id: str) -> None:
    #     """
    #     Delete all associated technical skills for a specific job
    #     """
    #     try:
    #         self._db.session.query(JobTechnicalSkill).filter_by(job_id=job_id).delete()
    #         self._db.session.commit()
    #     except SQLAlchemyError as e:
    #         self._db.session.rollback()
    #         raise e

    def bulk_insert(self, entities: List[JobTechnicalSkill]) -> List[JobTechnicalSkill]: 
        """ Bulk insert multiple job-related skills for performance efficiency """ 
        try: 
            self._db.session.bulk_save_objects(entities) 
            self._db.session.commit() 
            return entities 
        except SQLAlchemyError as e: 
            self._db.session.rollback() 
            log_and_raise(e) 

class JobSoftSkillRepository(BaseRepository[JobSoftSkill], JobDetailRepositoryMixin):
    def __init__(self):
        super().__init__(JobSoftSkill)

    # def get_by_job_id(self, job_id: str) -> List[JobSoftSkill]:
    #     """
    #     Get all associated soft skills for a specific job
    #     """
    #     try:
    #         return self._db.session.query(JobSoftSkill).filter_by(job_id=job_id).all()
    #     except SQLAlchemyError as e:
    #         self._db.session.rollback()
    #         raise e

    # def delete_by_job_id(self, job_id: str) -> None:
    #     """
    #     Delete all associated soft skills for a specific job
    #     """
    #     try:
    #         self._db.session.query(JobSoftSkill).filter_by(job_id=job_id).delete()
    #         self._db.session.commit()
    #     except SQLAlchemyError as e:
    #         self._db.session.rollback()
    #         raise e

    def bulk_insert(self, entities: List[JobSoftSkill]) -> List[JobSoftSkill]: 
        """ Bulk insert multiple job-related soft skills for performance efficiency """ 
        try: 
            self._db.session.bulk_save_objects(entities) 
            self._db.session.commit() 
            return entities 
        except SQLAlchemyError as e: 
            self._db.session.rollback() 
            log_and_raise(e)    


class JobEducationRepository(BaseRepository[JobEducation], JobDetailRepositoryMixin):
    def __init__(self):
        super().__init__(JobEducation)

    # def get_by_job_id(self, job_id: str) -> List[JobEducation]:
    #     """
    #     Get all associated education requirements for a specific job
    #     """
    #     try:
    #         return self._db.session.query(JobEducation).filter_by(job_id=job_id).all()
    #     except SQLAlchemyError as e:
    #         self._db.session.rollback()
    #         raise e

    # def delete_by_job_id(self, job_id: str) -> None:
    #     """
    #     Delete all associated education requirements for a specific job
    #     """
    #     try:
    #         self._db.session.query(JobEducation).filter_by(job_id=job_id).delete()
    #         self._db.session.commit()
    #     except SQLAlchemyError as e:
    #         self._db.session.rollback()
    #         raise e
    
    def bulk_insert(self, entities: List[JobEducation]) -> List[JobEducation]: 
        """ Bulk insert multiple job-related education entries for performance efficiency """ 
        try: 
            self._db.session.bulk_save_objects(entities) 
            self._db.session.commit() 
            return entities 
        except SQLAlchemyError as e: 
            self._db.session.rollback() 
            log_and_raise(e)
 

# You might want to use a RepositoryFactory if you need to manage these repositories centrally
# More repos for other entities may call for a more advanced factory pattern for more complex creation logic
class JobRepositoryFactory:
    # Factory for creating job related repositories with optional shared session handling
    def __init__(self, session=None):
        self.session = session
        
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
    
    # For atomic job creation with associated details.
    def create_job_with_details( self, 
                                job: Job, 
                                technical_skills: List[JobTechnicalSkill], 
                                soft_skills: List[JobSoftSkill],
                                education: List[JobEducation] ) -> Job: 
        """ Create a job along with all its technical skills, soft skills, and education details. """ 
        try: 
            job_repo = self.create_job_repository() 
            tech_skill_repo = self.create_technical_skill_repository() 
            soft_skill_repo = self.create_soft_skill_repository() 
            edu_repo = self.create_education_repository() 
            
            # Create the job 
            created_job = job_repo.create(job) 
            
            # Create associated job details 
            for skill in technical_skills: 
                skill.job_id = created_job.id 
            tech_skill_repo.bulk_insert(technical_skills) 
            
            for skill in soft_skills: 
                skill.job_id = created_job.id 
            soft_skill_repo.bulk_insert(soft_skills) 
            
            for edu in education: 
                edu.job_id = created_job.id 
            edu_repo.bulk_insert(education) 
            
            return created_job 
        
        except SQLAlchemyError as e: 
            self.session.rollback() 
            log_and_raise(e)