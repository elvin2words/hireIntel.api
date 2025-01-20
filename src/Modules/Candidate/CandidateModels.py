from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SqlEnum
from src.Modules.Interviews.InterviewModels import Interview

from src.config.DBModelsConfig import db


class CandidateStatus(Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)

    resume_url = db.Column(db.String(255), nullable=True)
    current_company = db.Column(db.String(255), nullable=True)
    current_position = db.Column(db.String(255), nullable=True)
    years_of_experience = db.Column(db.Integer, nullable=True)

    status = db.Column(SqlEnum(CandidateStatus), nullable=False, default=CandidateStatus.APPLIED)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Resume
    parsed_resume_data = db.Column(db.JSON, nullable=True)
    profiler_status = db.Column(db.String(20), nullable=True)

    # Relationships
    job = db.relationship('Job', backref='candidates', lazy='joined')
    interviews = db.relationship('Interview', backref='candidate', lazy='joined')

    def __repr__(self):
        return f"<Candidate {self.first_name} {self.last_name}>"