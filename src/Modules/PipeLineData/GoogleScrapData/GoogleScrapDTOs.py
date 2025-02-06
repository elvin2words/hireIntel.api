from marshmallow import Schema, fields, validate, post_dump
from src.Helpers.Utils import CamelCaseSchema


class CandidateProfessionalHandleDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(dump_only=True)
    handle = fields.Str(dump_only=True)
    handle_type = fields.Str(dump_only=True)
    handle_url = fields.Method("get_handle_url")
    verified = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_handle_url(self, obj):
        return obj.handle_url.value if hasattr(obj.handle_url, 'value') else str(obj.handle_url)

class CandidateCrimeDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    verified = fields.Bool(dump_only=True)
    url = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)