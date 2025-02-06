# candidate_models.py
from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SqlEnum, Index
from src.config.DBModelsConfig import db

class CandidateStatus(Enum):
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class CandidatePipelineStatus(Enum):
    # File watcher
    XML = "xml"
    XML_FAILED = "xml_failed"

    # Text Extraction
    EXTRACT_TEXT = "extract_text"
    EXTRACT_TEXT_FAILED = "extract_text_failed"

    # Google Scraping
    GOOGLE_SCRAPE = "google_scrape"
    GOOGLE_SCRAPE_FAILED = "google_scrape_failed"

    # LinkedIn Scraping
    LINKEDIN_SCRAPE = "linkedin_scrape"
    LINKEDIN_SCRAPE_FAILED = "linkedin_scrape_failed"

    # GitHub Scraping
    GITHUB_SCRAPE = "github_scrape"
    GITHUB_SCRAPE_FAILED = "github_scrape_failed"

    # Profile Creation
    PROFILE_CREATION = "profile_creation"
    PROFILE_CREATION_FAILED = "profile_creation_failed"

    # Profile created (Final) Status
    PROFILE_CREATED = "profile_created"
    PROFILE_CREATED_FAILED = "profile_created_failed"




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
    location = db.Column(db.String(255), nullable=True)

    status = db.Column(SqlEnum(CandidateStatus), nullable=False, default=CandidateStatus.APPLIED)
    pipeline_status = db.Column(SqlEnum(CandidatePipelineStatus), nullable=False, default=CandidatePipelineStatus.XML)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_candidate_status', 'status'),
        Index('idx_candidate_pipeline_status', 'pipeline_status'),
    )

    def __repr__(self):
        return f"<Candidate {self.first_name} {self.last_name}>"