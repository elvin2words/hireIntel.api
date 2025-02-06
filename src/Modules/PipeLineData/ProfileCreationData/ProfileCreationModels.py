import uuid
from datetime import datetime
from src.config.DBModelsConfig import db


class CandidateProfile(db.Model):
    __tablename__ = 'candidate_profiles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    matches = db.relationship('CandidateProfileMatch', backref='profile')
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)


class CandidateProfileMatch(db.Model):
    __tablename__ = 'candidate_profile_matches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = db.Column(db.String(36), db.ForeignKey('candidate_profiles.id'), nullable=False)
    job_id = db.Column(db.String(36), nullable=False)
    overall_match_score = db.Column(db.Float, nullable=False)
    overall_match_details = db.Column(db.String)
    diversity = db.Column(db.Boolean, nullable=True)

    technical_skills = db.relationship('CandidateProfileTechnicalSkills', backref='match', uselist=False)
    soft_skills = db.relationship('CandidateProfileSoftSkills', backref='match', uselist=False)
    experience = db.relationship('CandidateProfileExperience', backref='match', uselist=False)
    education = db.relationship('CandidateProfileEducation', backref='match', uselist=False)
    projects = db.relationship('CandidateProfileProjectsAndAchievements', backref='match', uselist=False)
    social_presence = db.relationship('CandidateProfileSocialPresence', backref='match', uselist=False)


class CandidateProfileTechnicalSkills(db.Model):
    __tablename__ = 'candidate_profile_technical_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_matches.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

    skill_matches = db.relationship('CandidateProfileTechnicalSkillMatch', backref='technical_skills')
    frameworks = db.relationship('CandidateProfileFrameworkAndTool', backref='technical_skills')


class CandidateProfileTechnicalSkillMatch(db.Model):
    __tablename__ = 'candidate_profile_technical_skill_matches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    technical_skills_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_technical_skills.id'),
                                    nullable=False)
    skill = db.Column(db.String, nullable=False)
    job_relevance = db.Column(db.Float, nullable=False)
    candidate_proficiency = db.Column(db.Float, nullable=False)


class CandidateProfileFrameworkAndTool(db.Model):
    __tablename__ = 'candidate_profile_frameworks_and_tools'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    technical_skills_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_technical_skills.id'),
                                    nullable=False)
    name = db.Column(db.String, nullable=False)
    proficiency = db.Column(db.Float, nullable=False)


class CandidateProfileSoftSkills(db.Model):
    __tablename__ = 'candidate_profile_soft_skills'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_matches.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

    skill_matches = db.relationship('CandidateProfileSoftSkillMatch', backref='soft_skills')


class CandidateProfileSoftSkillMatch(db.Model):
    __tablename__ = 'candidate_profile_soft_skill_matches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    soft_skills_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_soft_skills.id'), nullable=False)
    skill = db.Column(db.String, nullable=False)
    proficiency = db.Column(db.Float, nullable=False)


class CandidateProfileExperience(db.Model):
    __tablename__ = 'candidate_profile_experiences'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_matches.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    years_of_experience = db.Column(db.Float, nullable=False)

    industry_experiences = db.relationship('CandidateProfileIndustryExperience', backref='experience')
    relevant_roles = db.relationship('CandidateProfileRelevantRole', backref='experience')


class CandidateProfileIndustryExperience(db.Model):
    __tablename__ = 'candidate_profile_industry_experiences'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experience_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_experiences.id'), nullable=False)
    industry = db.Column(db.String, nullable=False)
    years = db.Column(db.Float, nullable=False)


class CandidateProfileRelevantRole(db.Model):
    __tablename__ = 'candidate_profile_relevant_roles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experience_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_experiences.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    company = db.Column(db.String, nullable=False)
    duration = db.Column(db.Float, nullable=False)


class CandidateProfileEducation(db.Model):
    __tablename__ = 'candidate_profile_educations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_matches.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

    degrees = db.relationship('CandidateProfileDegree', backref='education')


class CandidateProfileDegree(db.Model):
    __tablename__ = 'candidate_profile_degrees'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    education_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_educations.id'), nullable=False)
    degree = db.Column(db.String, nullable=False)
    major = db.Column(db.String, nullable=True)
    institution = db.Column(db.String, nullable=False)


class CandidateProfileProjectsAndAchievements(db.Model):
    __tablename__ = 'candidate_profile_projects_and_achievements'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_matches.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

    items = db.relationship('CandidateProfileProject', backref='projects')


class CandidateProfileProject(db.Model):
    __tablename__ = 'candidate_profile_projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    projects_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_projects_and_achievements.id'),
                            nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    relevance = db.Column(db.Float, nullable=False)


class CandidateProfileSocialPresence(db.Model):
    __tablename__ = 'candidate_profile_social_presence'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = db.Column(db.String(36), db.ForeignKey('candidate_profile_matches.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    linkedin_activity_score = db.Column(db.Float, nullable=False)
    github_contribution_score = db.Column(db.Float, nullable=False)
    blog_post_score = db.Column(db.Float, nullable=False)