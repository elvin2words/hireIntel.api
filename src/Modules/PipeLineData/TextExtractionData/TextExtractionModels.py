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
    email = db.Column(db.String(255), nullable=False, unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone_numbers = db.Column(db.JSON, nullable=True)  # Store multiple phone numbers
    address = db.Column(db.String(500), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    education = db.relationship('Education', backref='resume', lazy=True)
    experiences = db.relationship('WorkExperience', backref='resume', lazy=True)
    technical_skills = db.relationship('TechnicalSkill', backref='resume', lazy=True)
    soft_skills = db.relationship('SoftSkill', backref='resume', lazy=True)
    keywords = db.relationship('Keyword', backref='resume', lazy=True)

class Education(db.Model):
    __tablename__ = 'education'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    institution = db.Column(db.String(255), nullable=False)
    degree = db.Column(db.String(255), nullable=False)
    field_of_study = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    gpa = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)

class WorkExperience(db.Model):
    __tablename__ = 'work_experiences'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    employment_type = db.Column(SqlEnum(EmploymentType), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    achievements = db.Column(db.JSON, nullable=True)  # Store multiple achievements

class TechnicalSkill(db.Model):
    __tablename__ = 'technical_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    proficiency_level = db.Column(db.String(50), nullable=True)  # e.g., "Expert", "Intermediate"
    years_experience = db.Column(db.Integer, nullable=True)

class SoftSkill(db.Model):
    __tablename__ = 'soft_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)

class Keyword(db.Model):
    __tablename__ = 'keywords'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resumes.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)  # e.g., "Technology", "Industry", "Role"