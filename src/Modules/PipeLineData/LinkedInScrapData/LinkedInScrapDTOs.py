from marshmallow import Schema, fields, validate, post_dump
from src.Helpers.Utils import CamelCaseSchema

class LinkedInWorkExperienceDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    linked_in_profile_id = fields.Str(required=True)
    company = fields.Str(required=True)
    title = fields.Str(required=True)
    location = fields.Str(required=True)
    duration = fields.Str(required=True)
    description = fields.Str(allow_none=True)

class LinkedInEducationDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    linked_in_profile_id = fields.Str(required=True)
    school = fields.Str(required=True)
    degree = fields.Str(required=True)
    field = fields.Str(required=True)
    years = fields.Str(required=True)

class LinkedInProfileDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(required=True)
    username = fields.Str(required=True)
    full_name = fields.Str(required=True)
    headline = fields.Str(required=True)
    location = fields.Str(required=True)
    summary = fields.Str(required=True)
    verified = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    education = fields.Nested(LinkedInEducationDTO, many=True)
    experience = fields.Nested(LinkedInWorkExperienceDTO, many=True)
    skills = fields.List(fields.Str())