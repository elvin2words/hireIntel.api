from sqlalchemy import or_

from src.Modules.Candidate.CandidateModels import Candidate
from src.config.DBModelsConfig import db


class CandidateRepository:
    def __init__(self):
        self.__db = db

    def get_all_candidates(self, filters=None):
        query = self.__db.session.query(Candidate)

        if filters:
            if 'status' in filters:
                query = query.filter(Candidate.status == filters['status'])
            if 'job_id' in filters:
                query = query.filter(Candidate.job_id == filters['job_id'])

        return query.all()

    def get_candidate_by_id(self, candidate_id):
        return self.__db.session.query(Candidate).filter_by(id=candidate_id).first()

    def get_candidate_by_email(self, email):
        return self.__db.session.query(Candidate).filter_by(email=email).first()

    def save_candidate(self, candidate):
        self.__db.session.add(candidate)
        self.__db.session.commit()
        return candidate

    def update_candidate(self, candidate):
        self.__db.session.commit()
        return candidate

    def delete_candidate(self, candidate_id):
        candidate = self.get_candidate_by_id(candidate_id)
        if candidate:
            self.__db.session.delete(candidate)
            self.__db.session.commit()

    def get_candidates_for_job(self, job_id):
        return self.__db.session.query(Candidate).filter_by(job_id=job_id).all()

    def search_candidates(self, search_term):
        return self.__db.session.query(Candidate).filter(
            or_(
                Candidate.first_name.ilike(f'%{search_term}%'),
                Candidate.last_name.ilike(f'%{search_term}%'),
                Candidate.email.ilike(f'%{search_term}%'),
                Candidate.current_company.ilike(f'%{search_term}%')
            )
        ).all()