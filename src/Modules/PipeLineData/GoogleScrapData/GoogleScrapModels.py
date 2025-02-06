import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SqlEnum
from src.config.DBModelsConfig import db


class HandleType(Enum):
    LINKED_IN = "LINKED_IN"
    GITHUB = "GITHUB"


class CandidateProfessionalHandle(db.Model):
    __tablename__ = 'candidate_professional_handles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    handle = db.Column(db.String(36), nullable=False)
    handle_type = db.Column(SqlEnum(HandleType), nullable=False)
    handle_url = db.Column(db.String(36), nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class CandidateCrime(db.Model):
    __tablename__ = 'candidate_crimes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)