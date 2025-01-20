from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SqlEnum

from src.config.DBModelsConfig import db


class InterviewStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class InterviewType(Enum):
    PHONE_SCREENING = "phone_screening"
    TECHNICAL = "technical"
    HR = "hr"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    FINAL = "final"


class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    interviewer_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)

    interview_type = db.Column(SqlEnum(InterviewType), nullable=False)
    status = db.Column(SqlEnum(InterviewStatus), nullable=False, default=InterviewStatus.SCHEDULED)

    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255), nullable=True)  # Can be meeting link or physical location
    meeting_link = db.Column(db.String(255), nullable=True)

    notes = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Interview {self.id} for Candidate {self.candidate_id}>"