from marshmallow import Schema, fields, validate, post_dump

from src.Helpers.Utils import CamelCaseSchema
# from src.Modules.Interviews.InterviewDTOs import InterviewDTO
from src.Modules.Jobs.JobDTOs import JobDTO


class CandidateDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    job_id = fields.Str(required=True)

    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str(validate=validate.Length(max=20))

    resume_url = fields.Str(allow_none=True)
    current_company = fields.Str(allow_none=True)
    current_position = fields.Str(allow_none=True)
    years_of_experience = fields.Int(allow_none=True)
    location = fields.Str(allow_none=True)

    status = fields.Method("get_status")
    application_date = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Include related data
    job = fields.Nested(JobDTO, dump_only=True)
    # interviews = fields.Nested(InterviewDTO, many=True, dump_only=True)

    def get_status(self, obj):
        return obj.status.value if hasattr(obj.status, 'value') else str(obj.status)