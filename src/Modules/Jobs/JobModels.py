from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SqlEnum
from src.config.DBModelsConfig import db

"""
Enumerations for Job Attributes

"""


class JobStatus(Enum):
    # Represents the various statuses a job can have
    
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class ExperienceLevel(Enum):
    # Represents the experiences levels required for a job.
    
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"

class EmploymentType(Enum):
    # Represents the employment type for a job.
    
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


## Database Models
class Job(db.Model):
    # Represents the main jobs model with details for each listing
    __tablename__ = 'jobs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    remote_policy = db.Column(db.String(50), nullable=True)
    
    employment_type = db.Column(SqlEnum(EmploymentType), nullable=False)
    experience_level = db.Column(SqlEnum(ExperienceLevel), nullable=False)
    min_experience_years = db.Column(db.Integer, nullable=False)
    max_experience_years = db.Column(db.Integer, nullable=True)
    
    min_salary = db.Column(db.Float, nullable=True)
    max_salary = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    
    candidates_needed = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(SqlEnum(JobStatus), nullable=False, default=JobStatus.DRAFT)
    application_deadline = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # utcnow > deprecated ???
    # created_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.utc)) 
    # updated_at = db.Column(db.DateTime, default=datetime.now(datetime.timezone.utc), 
    #                        onupdate=datetime.now(datetime.timezone.utc))
    published_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        # String representation of a job object
        return f"<Job {self.title}>"


class JobTechnicalSkill(db.Model):
    # Represents the technical skills required for a job
    __tablename__ = 'job_technical_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    years_experience = db.Column(db.Integer, nullable=True)
    is_required = db.Column(db.Boolean, default=True)


class JobSoftSkill(db.Model):
    # Represents the soft skills required for a job
    __tablename__ = 'job_soft_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)


class JobEducation(db.Model):
    # Represents the educational qualifications required for a job
    __tablename__ = 'job_education'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = db.Column(db.String(36), db.ForeignKey('jobs.id'), nullable=False)
    degree_level = db.Column(db.String(100), nullable=False)  # e.g., "Bachelor's", "Master's"
    field_of_study = db.Column(db.String(255), nullable=False)
    is_required = db.Column(db.Boolean, default=True)