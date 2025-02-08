import uuid
from datetime import datetime

from src.config.DBModelsConfig import db


class EmailNotification(db.Model):
    __tablename__ = 'email_notifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # 'accepted' or 'rejected'
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, sent, failed