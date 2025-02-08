from datetime import datetime
from typing import List, Optional, Dict
from src.Helpers.BaseRepository import BaseRepository
from src.Modules.Interviews.InterviewModels import InterviewSchedule, InterviewStatus


class InterviewScheduleRepository(BaseRepository[InterviewSchedule]):
    def __init__(self):
        super().__init__(InterviewSchedule)

    def get_by_candidate_id(self, candidate_id: str) -> Optional[InterviewSchedule]:
        """Get interview schedule by candidate ID"""
        return self._model.query.filter_by(candidate_id=candidate_id).first()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[InterviewSchedule]:
        """Get all schedules within a date range"""
        return self._model.query.filter(
            InterviewSchedule.start_datetime >= start_date,
            InterviewSchedule.end_datetime <= end_date
        ).all()

    def get_with_filters(self, filters: Dict) -> List[InterviewSchedule]:
        """Get schedules with applied filters"""
        query = self._model.query

        if filters.get('status'):
            query = query.filter_by(status=InterviewStatus(filters['status']))

        if filters.get('candidate_id'):
            query = query.filter_by(candidate_id=filters['candidate_id'])

        if filters.get('start_date') and filters.get('end_date'):
            query = query.filter(
                InterviewSchedule.start_datetime >= filters['start_date'],
                InterviewSchedule.end_datetime <= filters['end_date']
            )

        return query.all()

    def update_status(self, schedule_id: str, status: InterviewStatus) -> Optional[InterviewSchedule]:
        """Update the status of an interview schedule"""
        schedule = self.get_by_id(schedule_id)
        if schedule:
            schedule.status = status
            return self.update(schedule)
        return None


# class EmailNotificationRepository(BaseRepository[EmailNotification]):
#     def __init__(self):
#         super().__init__(EmailNotification)
#
#     def get_by_candidate_id(self, candidate_id: str) -> List[EmailNotification]:
#         """Get all email notifications for a candidate"""
#         return self._model.query.filter_by(candidate_id=candidate_id).all()
#
#     def create_notification(self, notification_data: Dict) -> EmailNotification:
#         """Create a new email notification"""
#         notification = EmailNotification(**notification_data)
#         return self.create(notification)