import uuid
from datetime import datetime

from src.config.DBModelsConfig import db

class LinkedInProfile(db.Model):
    __tablename__ = 'linked_in_profiles'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    username = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    headline = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    summary = db.Column(db.String, nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    education = db.relationship('LinkedInEducation', backref='profile', lazy=True)
    experience = db.relationship('LinkedInWorkExperience', backref='profile', lazy=True)
    skills = db.Column(db.JSON, nullable=True)

class LinkedInWorkExperience(db.Model):
    __tablename__ = 'linkedin_work_experiences'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    linked_in_profile_id = db.Column(db.String(36), db.ForeignKey('linked_in_profiles.id'), nullable=False)
    company = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    duration = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)

class LinkedInEducation(db.Model):
    __tablename__ = 'linkedin_educations'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    linked_in_profile_id = db.Column(db.String(36), db.ForeignKey('linked_in_profiles.id'), nullable=False)
    school = db.Column(db.String, nullable=False)
    degree = db.Column(db.String, nullable=False)
    field = db.Column(db.String, nullable=False)
    years = db.Column(db.String, nullable=False)