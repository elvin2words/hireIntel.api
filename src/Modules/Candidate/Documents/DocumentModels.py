from dataclasses import dataclass
from datetime import datetime
import uuid
from typing import Optional, List

from src.config.DBModelsConfig import db

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # e.g., 'resume', 'cover_letter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    candidate = db.relationship('Candidate', backref='documents')

# Data classes for structured data
@dataclass
class PersonInfo:
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    current_company: Optional[str]
    current_position: Optional[str]
    years_of_experience: Optional[int]
    job_id: str

@dataclass
class DocumentInfo:
    original_name: str
    file_path: str
    document_type: str

@dataclass
class CandidateDocument:
    person_info: PersonInfo
    documents: List[DocumentInfo]