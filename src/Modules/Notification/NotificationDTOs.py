from marshmallow import fields, validate

from src.Helpers.Utils import CamelCaseSchema
from src.Modules.Candidate.CandidateDTOs import CandidateDTO


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