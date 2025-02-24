from typing import List, Dict

from src.Helpers.BaseRepository import BaseRepository
from src.Modules.Notification.NotificationModels import EmailNotification

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from datetime import datetime

class EmailNotificationRepository(BaseRepository[EmailNotification]):
    def __init__(self):
        # Initialize the repository with the EmailNotification model.
        super().__init__(EmailNotification)

    def get_by_candidate_id(self, candidate_id: str) -> List[EmailNotification]:
        """Get a List of all email notifications for a candidate"""
        try:
            return self._model.query.filter_by(candidate_id=candidate_id).all()
        except SQLAlchemyError as e:
            # Log the error 
            print(f"Error fetching notifications: {e}")
            return []

    def create_notification(self, notification_data: Dict) -> EmailNotification:
        """Create a new email notification"""
        try:
            notification = EmailNotification(**notification_data)
            return self.create(notification)
        except SQLAlchemyError as e:
            # Log the error
            print(f"Error creating notification: {e}")
            return None
        
    def get_by_status(self, status: str, page: int = 1, per_page: int = 20) -> List[EmailNotification]:
        """
        Retrieve all email notifications with a specific status.
        Args:
            status (str): The status to filter by (e.g., 'pending', 'sent', 'failed').
            page (int): The page number for pagination (default is 1).
            per_page (int): The number of items per page (default is 20).
        """
        try:
            return self._model.query.filter_by(status=status).paginate(page, per_page, False).items
        except SQLAlchemyError as e:
            # Log the error
            print(f"Error fetching notifications by status: {e}")
            return []

    def soft_delete(self, notification_id: str) -> bool:
        """
        Mark an email notification as deleted without removing it from the database.
        Args:
            notification_id (str): The ID of the notification to soft delete.
        """
        try:
            notification = self._model.query.get(notification_id)
            if notification:
                notification.deleted_at = datetime.utcnow()  # Mark as deleted by setting the timestamp
                self.db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            # Log the error
            print(f"Error performing soft delete: {e}")
            return False