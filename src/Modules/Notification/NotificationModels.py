import uuid
from datetime import datetime
from src.config.DBModelsConfig import db


# Database model for email notifications
class EmailNotification(db.Model):
    __tablename__ = 'email_notifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = db.Column(db.String(36), db.ForeignKey('candidates.id'), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # 'accepted' or 'rejected'
    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, sent, failed
    deleted_at = db.Column(db.DateTime, nullable=True) # for soft deletes
    
    def __repr__(self):
        ##Provides a human-readable representation of the EmailNotification object
        
        return f"<EmailNotification(id='{self.id}', candidate_id='{self.candidate_id}', status='{self.status}', sent_at='{self.sent_at}')>"
