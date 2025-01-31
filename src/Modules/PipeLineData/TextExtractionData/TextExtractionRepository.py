from typing import Optional, List, Dict

from src.Helpers.base_repository import BaseRepository
from src.Modules.PipeLineData.TextExtractionData.TextExtractionModels import (
    Resume, Education, WorkExperience, TechnicalSkill, SoftSkill, Keyword
)
from sqlalchemy.exc import SQLAlchemyError


class ResumeRepository(BaseRepository[Resume]):
    def __init__(self):
        super().__init__(Resume)

    def get_by_email(self, email: str) -> Optional[Resume]:
        """
        Get a resume by email address
        """
        try:
            return self._db.session.query(self._model).filter_by(email=email).first()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

    def get_all_with_filters(self, filters: Optional[Dict] = None) -> List[Resume]:
        """
        Get all resumes with optional filtering
        """
        try:
            query = self._db.session.query(self._model)

            if filters:
                if 'email' in filters:
                    query = query.filter(self._model.email.ilike(f"%{filters['email']}%"))
                if 'skill' in filters:
                    query = query.join(TechnicalSkill).filter(
                        TechnicalSkill.skill_name.ilike(f"%{filters['skill']}%")
                    )
                if 'full_name' in filters:
                    query = query.filter(self._model.full_name.ilike(f"%{filters['full_name']}%"))

            return query.all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class EducationRepository(BaseRepository[Education]):
    def __init__(self):
        super().__init__(Education)

    def get_by_resume_id(self, resume_id: str) -> List[Education]:
        """
        Get all education records for a specific resume
        """
        try:
            return self._db.session.query(self._model).filter_by(resume_id=resume_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class WorkExperienceRepository(BaseRepository[WorkExperience]):
    def __init__(self):
        super().__init__(WorkExperience)

    def get_by_resume_id(self, resume_id: str) -> List[WorkExperience]:
        """
        Get all work experiences for a specific resume
        """
        try:
            return self._db.session.query(self._model).filter_by(resume_id=resume_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class TechnicalSkillRepository(BaseRepository[TechnicalSkill]):
    def __init__(self):
        super().__init__(TechnicalSkill)

    def get_by_resume_id(self, resume_id: str) -> List[TechnicalSkill]:
        """
        Get all technical skills for a specific resume
        """
        try:
            return self._db.session.query(self._model).filter_by(resume_id=resume_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class SoftSkillRepository(BaseRepository[SoftSkill]):
    def __init__(self):
        super().__init__(SoftSkill)

    def get_by_resume_id(self, resume_id: str) -> List[SoftSkill]:
        """
        Get all soft skills for a specific resume
        """
        try:
            return self._db.session.query(self._model).filter_by(resume_id=resume_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e


class KeywordRepository(BaseRepository[Keyword]):
    def __init__(self):
        super().__init__(Keyword)

    def get_by_resume_id(self, resume_id: str) -> List[Keyword]:
        """
        Get all keywords for a specific resume
        """
        try:
            return self._db.session.query(self._model).filter_by(resume_id=resume_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e