from marshmallow import fields, validate, post_dump
from src.Helpers.Utils import CamelCaseSchema
from src.Modules.Candidate.CandidateDTOs import CandidateDTO

class InterviewScheduleDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(required=True)
    interviewer_id = fields.Str(required=True)
    start_datetime = fields.DateTime(required=True)
    end_datetime = fields.DateTime(required=True)
    status = fields.Method("get_status")
    location = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)
    # schedule_metadata = fields.Dict(allow_none=True)
    meeting_link = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Include related data
    candidate = fields.Nested(CandidateDTO, dump_only=True)

    def get_status(self, obj):
        return obj.status.value if hasattr(obj.status, 'value') else str(obj.status)

class EmailNotificationDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(required=True)
    email_type = fields.Str(required=True, validate=validate.OneOf(['accepted', 'rejected']))
    subject = fields.Str(required=True, validate=validate.Length(max=255))
    content = fields.Str(required=True)
    sent_at = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True, validate=validate.OneOf(['pending', 'sent', 'failed']))

    # Include related data
    candidate = fields.Nested(CandidateDTO, dump_only=True)
