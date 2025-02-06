# models.py
from src.config.DBModelsConfig import db
from src.Modules.Jobs.JobModels import Job
from src.Modules.Candidate.CandidateModels import Candidate

# Import any other model files here

# Define relationships
Job.candidates = db.relationship('Candidate', back_populates='job', lazy='joined')
Job.technical_skills = db.relationship('JobTechnicalSkill', backref='job', lazy=True, cascade="all, delete-orphan")
Job.soft_skills = db.relationship('JobSoftSkill', backref='job', lazy=True, cascade="all, delete-orphan")
Job.education_requirements = db.relationship('JobEducation', backref='job', lazy=True, cascade="all, delete-orphan")

Candidate.job = db.relationship('Job', back_populates='candidates', lazy='joined')
# Candidate.interviews = db.relationship('Interview', backref='candidate', lazy='joined')

# Function to initialize all models
def init_models():
    # Import all models here to ensure they're registered with SQLAlchemy
    return [Job, Candidate]  # Add other models to this list