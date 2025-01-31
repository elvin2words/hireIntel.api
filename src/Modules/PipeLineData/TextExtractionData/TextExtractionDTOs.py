from marshmallow import Schema, fields, validate, post_dump
from src.Helpers.Utils import CamelCaseSchema

class EducationDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    institution = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    degree = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    field_of_study = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True)
    gpa = fields.Float(allow_none=True)
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)

class WorkExperienceDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    company = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    position = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    employment_type = fields.Method("get_employment_type")
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True)
    is_current = fields.Boolean(default=False)
    location = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    achievements = fields.List(fields.Str(), allow_none=True)

    def get_employment_type(self, obj):
        return obj.employment_type.value if hasattr(obj.employment_type, 'value') else str(obj.employment_type)

class TechnicalSkillDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    skill_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    proficiency_level = fields.Str(allow_none=True)
    years_experience = fields.Int(allow_none=True)

class SoftSkillDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    skill_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

class KeywordDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    keyword = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category = fields.Str(allow_none=True)

class ResumeDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    candidate_id = fields.Str(required=True)
    email = fields.Email(required=True)
    full_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    phone_numbers = fields.List(fields.Str(), allow_none=True)
    address = fields.Str(allow_none=True)
    linkedin_url = fields.Url(allow_none=True)
    github_url = fields.Url(allow_none=True)
    portfolio_url = fields.Url(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    education = fields.Nested(EducationDTO, many=True)
    experiences = fields.Nested(WorkExperienceDTO, many=True)
    technical_skills = fields.Nested(TechnicalSkillDTO, many=True)
    soft_skills = fields.Nested(SoftSkillDTO, many=True)
    keywords = fields.Nested(KeywordDTO, many=True)