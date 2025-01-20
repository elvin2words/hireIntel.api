from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SqlEnum

from src.config.DBModelsConfig import db


class JobStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"

class ExperienceLevel(Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"

class EmploymentType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"

class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    remote_policy = db.Column(db.String(50), nullable=True)  # e.g., "Remote", "Hybrid", "On-site"
    employment_type = db.Column(SqlEnum(EmploymentType), nullable=False)
    experience_level = db.Column(SqlEnum(ExperienceLevel), nullable=False)
    min_experience_years = db.Column(db.Integer, nullable=False)
    max_experience_years = db.Column(db.Integer, nullable=True)
    min_salary = db.Column(db.Float, nullable=True)
    max_salary = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(3), nullable=True)  # e.g., "USD", "EUR"
    candidates_needed = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(SqlEnum(JobStatus), nullable=False, default=JobStatus.DRAFT)
    application_deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    technical_skills = db.relationship('JobTechnicalSkill', backref='job', lazy=True, cascade="all, delete-orphan")
    soft_skills = db.relationship('JobSoftSkill', backref='job', lazy=True, cascade="all, delete-orphan")
    education_requirements = db.relationship('JobEducation', backref='job', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.title}>"

class JobTechnicalSkill(db.Model):
    __tablename__ = 'job_technical_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    years_experience = db.Column(db.Integer, nullable=True)
    is_required = db.Column(db.Boolean, default=True)

class JobSoftSkill(db.Model):
    __tablename__ = 'job_soft_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)

class JobEducation(db.Model):
    __tablename__ = 'job_education'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    degree_level = db.Column(db.String(100), nullable=False)  # e.g., "Bachelor's", "Master's"
    field_of_study = db.Column(db.String(255), nullable=False)
    is_required = db.Column(db.Boolean, default=True)