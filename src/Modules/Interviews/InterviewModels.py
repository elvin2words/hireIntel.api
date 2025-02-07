from enum import Enum
from datetime import datetime
import uuid
from src.config.DBModelsConfig import db

class InterviewStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InterviewSchedule(db.Model):
    __tablename__ = 'interview_schedules'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    interviewer_id = db.Column(db.String(36), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    location = db.Column(db.String(255), nullable=True)  # Can be meeting link or physical location
    notes = db.Column(db.Text, nullable=True)
    meeting_link = db.Column(db.String(255), nullable=True)
    # schedule_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailNotification(db.Model):
    __tablename__ = 'email_notifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # 'accepted' or 'rejected'
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed