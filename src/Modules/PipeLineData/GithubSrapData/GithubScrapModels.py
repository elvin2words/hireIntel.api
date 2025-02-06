import uuid
from datetime import datetime

from src.config.DBModelsConfig import db

class GitHubProfile(db.Model):
    __tablename__ = 'github_profiles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    bio = db.Column(db.String, nullable=True)
    company = db.Column(db.String, nullable=True)
    location = db.Column(db.String, nullable=True)
    blog = db.Column(db.String, nullable=True)
    twitter_username = db.Column(db.String, nullable=True)
    avatar_url = db.Column(db.String, nullable=True)

    followers = db.Column(db.Integer, nullable=False, default=0)
    following = db.Column(db.Integer, nullable=False, default=0)
    public_repos = db.Column(db.Integer, nullable=False, default=0)
    public_gists = db.Column(db.Integer, nullable=False, default=0)
    total_stars_earned = db.Column(db.Integer, nullable=False, default=0)
    contributions_last_year = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    stats = db.Column(db.JSON, nullable=True)
    dates = db.Column(db.JSON, nullable=True)
    urls = db.Column(db.JSON, nullable=True)
    additional_info = db.Column(db.JSON, nullable=True)

    # Relationships
    repositories = db.relationship('GithubRepository', backref='profile', lazy=True)

class GithubRepository(db.Model):
    __tablename__ = 'github_repositories'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    github_profile_id = db.Column(db.String(36), db.ForeignKey('github_profiles.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    full_name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    homepage = db.Column(db.String, nullable=True)
    language = db.Column(db.String, nullable=True)
    stars = db.Column(db.Integer, nullable=False, default=0)
    watchers = db.Column(db.Integer, nullable=False, default=0)
    forks = db.Column(db.Integer, nullable=False, default=0)
    open_issues = db.Column(db.Integer, nullable=False, default=0)
    size = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    pushed_at = db.Column(db.DateTime, nullable=True)
    is_fork = db.Column(db.Boolean, nullable=False, default=False)

    languages_breakdown = db.Column(db.JSON, nullable=True)
    stats = db.Column(db.JSON, nullable=True)
    dates = db.Column(db.JSON, nullable=True)
    urls = db.Column(db.JSON, nullable=True)
    features = db.Column(db.JSON, nullable=True)
    branch = db.Column(db.JSON, nullable=True)
    license = db.Column(db.String, nullable=True)
    latest_commits = db.Column(db.JSON, nullable=True)
    top_contributors = db.Column(db.JSON, nullable=True)