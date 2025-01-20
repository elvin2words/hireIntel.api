from src.Modules.Jobs.JobModels import Job
from src.config.DBModelsConfig import db


class JobRepository:
    def __init__(self):
        self.__db = db

    def get_all_jobs(self, filters=None):
        query = self.__db.session.query(Job)

        if filters:
            if 'status' in filters:
                query = query.filter(Job.status == filters['status'])
            if 'experience_level' in filters:
                query = query.filter(Job.experience_level == filters['experience_level'])
            if 'employment_type' in filters:
                query = query.filter(Job.employment_type == filters['employment_type'])

        return query.all()

    def get_job_by_id(self, job_id):
        return self.__db.session.query(Job).filter_by(id=job_id).first()

    def save_job(self, job):
        self.__db.session.add(job)
        self.__db.session.commit()
        return job

    def update_job(self, job):
        self.__db.session.commit()
        return job

    def delete_job(self, job_id):
        job = self.get_job_by_id(job_id)
        if job:
            self.__db.session.delete(job)
            self.__db.session.commit()

    def save_technical_skill(self, skill):
        self.__db.session.add(skill)
        self.__db.session.commit()

    def save_soft_skill(self, skill):
        self.__db.session.add(skill)
        self.__db.session.commit()

    def save_education_requirement(self, education):
        self.__db.session.add(education)
        self.__db.session.commit()