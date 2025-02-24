from marshmallow import Schema, fields, validate, post_dump, ValidationError

from src.Helpers.Utils import CamelCaseSchema

from datetime import datetime


'''
    Defining Data Transfer Objects for both serialization and data validation
     
'''

class JobTechnicalSkillDTO(CamelCaseSchema):
    # Represents the Job Technical Skills Requirements
    
    id = fields.Str(dump_only=True)
    skill_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    years_experience = fields.Int(validate=validate.Range(min=0))
    is_required = fields.Boolean(default=True)


class JobSoftSkillDTO(CamelCaseSchema):
    # Represents the Job Soft Skills Requirements
    
    id = fields.Str(dump_only=True)
    skill_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))


class JobEducationDTO(CamelCaseSchema):
    # Represents the Job Education Requirements
    
    id = fields.Str(dump_only=True)
    degree_level = fields.Str(required=True)
    field_of_study = fields.Str(required=True)
    is_required = fields.Boolean(default=True)


class JobDTO(CamelCaseSchema):
    # Represents the detailed info of a job listing
    
    id = fields.Str(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=True)
    company_id = fields.Str(required=True)
    department = fields.Str(allow_none=True)
    location = fields.Str(required=True)
    remote_policy = fields.Str(allow_none=True)
    
    employment_type = fields.Method("get_employment_type")
    experience_level = fields.Method("get_experience_level")
    min_experience_years = fields.Int(required=True, validate=validate.Range(min=0))
    max_experience_years = fields.Int(allow_none=True)
    
    min_salary = fields.Float(allow_none=True)
    max_salary = fields.Float(allow_none=True)
    currency = fields.Str(allow_none=True, validate=validate.Length(equal=3))
    
    candidates_needed = fields.Int(required=True, validate=validate.Range(min=1))
    status = fields.Method("get_status")
    # application_deadline = fields.DateTime(allow_none=True)
    application_deadline = fields.DateTime(allow_none=True, validate=lambda value: JobDTO.validate_future_date(value))
        
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    published_at = fields.DateTime(dump_only=True)

    technical_skills = fields.Nested(JobTechnicalSkillDTO, many=True)
    soft_skills = fields.Nested(JobSoftSkillDTO, many=True)
    education_requirements = fields.Nested(JobEducationDTO, many=True)

    def get_status(self, obj):
        # Returns string representation of job status
        return obj.status.value if hasattr(obj.status, 'value') else str(obj.status)

    def get_employment_type(self, obj):
        # Returns the string represenatation of the employment type
        return obj.employment_type.value if hasattr(obj.employment_type, 'value') else str(obj.employment_type)

    def get_experience_level(self, obj):
        # Returns the string representation of the experience level
        return obj.experience_level.value if hasattr(obj.experience_level, 'value') else str(obj.experience_level)
    
    # Validation and Post-processing
    @post_dump
    def remove_null_fields(self, data, many):
        # Removes fields with null values from the serialized output
        return {key:value for key, value in data.items() if value is not None}
    
    @staticmethod
    def validate_future_date(value):
        # Validates that the date is in the future
        if value and value <= datetime.now(datetime.timezone.utc):
            raise ValidationError("Application deadline must be a future date")