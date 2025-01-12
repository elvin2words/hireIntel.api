from enum import Enum

from datetime import datetime
from sqlalchemy import Enum as SqlEnum

from src.config.DBModelsConfig import db


# Enums
class Role(Enum):
    ADMIN = 'ADMIN'
    USER = 'USER'


class TokenType(Enum):
    ACCESS = 'ACCESS'
    REFRESH = 'REFRESH'


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(36), primary_key=True)
    first_name = db.Column(db.String(36), nullable=False)
    last_name = db.Column(db.String(36), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)  # Hashed password
    role = db.Column(SqlEnum(Role), nullable=False)  # Role (e.g., customer, admin)

    def __repr__(self):
        return f"<User {self.name}>"


class Token(db.Model):
    __tablename__ = 'tokens'

    token_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=True, index=True)
    token = db.Column(db.String(128), nullable=False)
    token_type = db.Column(SqlEnum(TokenType), nullable=False)
    is_expired = db.Column(db.Boolean, nullable=False)
    is_revoked = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Token {self.token_id}, Type: {self.token_type}>"


class Profile(db.Model):
    __tablename__ = 'profiles'

    profile_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False, index=True)
    sex = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(100), nullable=False)
    profession = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    about_me = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Profile {self.profile_id}>"

