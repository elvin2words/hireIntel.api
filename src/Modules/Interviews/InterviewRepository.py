import datetime

from src.Modules.Interviews.InterviewModels import Interview, InterviewStatus
from src.config.DBModelsConfig import db


class InterviewRepository:
    def __init__(self):
        self.__db = db

    def get_all_interviews(self, filters=None):
        query = self.__db.session.query(Interview)

        if filters:
            if 'status' in filters:
                query = query.filter(Interview.status == filters['status'])
            if 'interview_type' in filters:
                query = query.filter(Interview.interview_type == filters['interview_type'])
            if 'candidate_id' in filters:
                query = query.filter(Interview.candidate_id == filters['candidate_id'])
            if 'interviewer_id' in filters:
                query = query.filter(Interview.interviewer_id == filters['interviewer_id'])
            if 'job_id' in filters:
                query = query.filter(Interview.job_id == filters['job_id'])

        return query.all()

    def get_interview_by_id(self, interview_id):
        return self.__db.session.query(Interview).filter_by(id=interview_id).first()

    def save_interview(self, interview):
        self.__db.session.add(interview)
        self.__db.session.commit()
        return interview

    def update_interview(self, interview):
        self.__db.session.commit()
        return interview

    def delete_interview(self, interview_id):
        interview = self.get_interview_by_id(interview_id)
        if interview:
            self.__db.session.delete(interview)
            self.__db.session.commit()

    def check_interviewer_availability(self, interviewer_id, scheduled_date, duration_minutes):
        """Check if interviewer has any conflicting interviews"""
        end_time = scheduled_date + datetime.timedelta(minutes=duration_minutes)

        conflicts = self.__db.session.query(Interview).filter(
            Interview.interviewer_id == interviewer_id,
            Interview.status == InterviewStatus.SCHEDULED,
            Interview.scheduled_date < end_time,
            (Interview.scheduled_date + datetime.timedelta(minutes=Interview.duration_minutes)) > scheduled_date
        ).all()

        return len(conflicts) == 0