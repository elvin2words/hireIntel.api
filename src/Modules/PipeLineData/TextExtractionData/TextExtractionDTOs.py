from marshmallow import Schema, fields, validate
from src.Helpers.Utils import CamelCaseSchema

class PersonalInformationDTO(CamelCaseSchema):
    full_name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone_numbers = fields.List(fields.Str(), allow_none=True)
    address = fields.Str(allow_none=True)
    linkedin_url = fields.Str(allow_none=True)
    github_url = fields.Str(allow_none=True)
    portfolio_url = fields.Str(allow_none=True)

class EducationDTO(CamelCaseSchema):
    institution = fields.Str(required=True)
    degree = fields.Str(required=True)
    field_of_study = fields.Str(allow_none=True)
    start_date = fields.Str(allow_none=True)  # Changed to string
    end_date = fields.Str(allow_none=True)    # Changed to string
    gpa = fields.Float(allow_none=True)
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)

class WorkExperienceDTO(CamelCaseSchema):
    company = fields.Str(required=True)
    position = fields.Str(required=True)
    employment_type = fields.Str(allow_none=True)
    start_date = fields.Str(allow_none=True)  # Changed to string
    end_date = fields.Str(allow_none=True)    # Changed to string
    is_current = fields.Boolean(allow_none=True)
    location = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    achievements = fields.List(fields.Str(), allow_none=True)

class TechnicalSkillDTO(CamelCaseSchema):
    skill_name = fields.Str(required=True)
    proficiency_level = fields.Str(allow_none=True)
    years_experience = fields.Int(allow_none=True)

class SoftSkillDTO(CamelCaseSchema):
    skill_name = fields.Str(required=True)

class KeywordDTO(CamelCaseSchema):
    keyword = fields.Str(required=True)
    category = fields.Str(allow_none=True)

class ResumeDTO(CamelCaseSchema):
    personal_information = fields.Nested(PersonalInformationDTO, required=True)
    education = fields.Nested(EducationDTO, many=True, required=True)
    work_experience = fields.Nested(WorkExperienceDTO, many=True, required=True)
    technical_skills = fields.Nested(TechnicalSkillDTO, many=True, required=True)
    soft_skills = fields.Nested(SoftSkillDTO, many=True, required=True)
    keywords = fields.Nested(KeywordDTO, many=True, required=True)