from typing import List, Dict

from src.Helpers.BaseRepository import BaseRepository
from src.Modules.Notification.NotificationModels import EmailNotification


class EmailNotificationRepository(BaseRepository[EmailNotification]):
    def __init__(self):
        super().__init__(EmailNotification)

    def get_by_candidate_id(self, candidate_id: str) -> List[EmailNotification]:
        """Get all email notifications for a candidate"""
        return self._model.query.filter_by(candidate_id=candidate_id).all()

    def create_notification(self, notification_data: Dict) -> EmailNotification:
        """Create a new email notification"""
        notification = EmailNotification(**notification_data)
        return self.create(notification)