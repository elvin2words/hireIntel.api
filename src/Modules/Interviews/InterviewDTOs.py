from marshmallow import Schema, fields, validate, post_dump

from src.Helpers.Utils import CamelCaseSchema
from src.Modules.Candidate.CandidateDTOs import CandidateDTO
from src.Modules.Jobs.JobDTOs import JobDTO


class InterviewDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    job_id = fields.Str(required=True)
    candidate_id = fields.Str(required=True)
    interviewer_id = fields.Str(required=True)

    interview_type = fields.Method("get_interview_type")
    status = fields.Method("get_status")

    scheduled_date = fields.DateTime(required=True)
    duration_minutes = fields.Int(required=True, validate=validate.Range(min=15, max=180))
    location = fields.Str(allow_none=True)
    meeting_link = fields.Str(allow_none=True)

    notes = fields.Str(allow_none=True)
    feedback = fields.Str(allow_none=True)
    score = fields.Float(allow_none=True, validate=validate.Range(min=0, max=10))

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    cancelled_at = fields.DateTime(dump_only=True)
    cancellation_reason = fields.Str(allow_none=True)

    # Include related data
    job = fields.Nested(JobDTO, dump_only=True)
    candidate = fields.Nested(CandidateDTO, dump_only=True)

    def get_status(self, obj):
        return obj.status.value if hasattr(obj.status, 'value') else str(obj.status)

    def get_interview_type(self, obj):
        return obj.interview_type.value if hasattr(obj.interview_type, 'value') else str(obj.interview_type)