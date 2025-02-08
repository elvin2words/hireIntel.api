from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SqlEnum
from src.config.DBModelsConfig import db


class EmploymentType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class Resume(db.Model):
    __tablename__ = 'resumes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)

    # Personal Information
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone_numbers = db.Column(db.JSON, nullable=True)
    address = db.Column(db.String(500), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_handle = db.Column(db.String(255), nullable=True)
    github_handle = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    education = db.relationship('Education', backref='resume', lazy=True, cascade="all, delete-orphan")
    work_experience = db.relationship('WorkExperience', backref='resume', lazy=True, cascade="all, delete-orphan")
    technical_skills = db.relationship('TechnicalSkill', backref='resume', lazy=True, cascade="all, delete-orphan")
    soft_skills = db.relationship('SoftSkill', backref='resume', lazy=True, cascade="all, delete-orphan")
    keywords = db.relationship('Keyword', backref='resume', lazy=True, cascade="all, delete-orphan")


class Education(db.Model):
    __tablename__ = 'resume_education'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    institution = db.Column(db.String(255), nullable=False)
    degree = db.Column(db.String(255), nullable=False)
    field_of_study = db.Column(db.String(255), nullable=True)  # Changed to nullable
    start_date = db.Column(db.String(10), nullable=True)  # Changed to string format YYYY-MM-DD
    end_date = db.Column(db.String(10), nullable=True)  # Changed to string format YYYY-MM-DD
    gpa = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)


class WorkExperience(db.Model):
    __tablename__ = 'resume_work_experiences'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    employment_type = db.Column(db.String(50), nullable=True)  # Changed to string
    start_date = db.Column(db.String(10), nullable=True)  # Changed to string format YYYY-MM-DD
    end_date = db.Column(db.String(10), nullable=True)  # Changed to string format YYYY-MM-DD
    is_current = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    achievements = db.Column(db.JSON, nullable=True)


class TechnicalSkill(db.Model):
    __tablename__ = 'resume_technical_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency_level = db.Column(db.String(50), nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)


class SoftSkill(db.Model):
    __tablename__ = 'resume_soft_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)


class Keyword(db.Model):
    __tablename__ = 'resume_keywords'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)