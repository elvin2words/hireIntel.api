from marshmallow import Schema, fields, validate, post_dump
from src.Helpers.Utils import CamelCaseSchema


class CandidateProfileDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    matches = fields.Nested('CandidateProfileMatchDTO', many=True)


class CandidateProfileMatchDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    profile_id = fields.Str(required=True)
    job_id = fields.Str(required=True)
    overall_match_score = fields.Float(required=True)
    overall_match_details = fields.Str()
    diversity = fields.Bool()

    technical_skills = fields.Nested('CandidateProfileTechnicalSkillsDTO')
    soft_skills = fields.Nested('CandidateProfileSoftSkillsDTO')
    experience = fields.Nested('CandidateProfileExperienceDTO')
    education = fields.Nested('CandidateProfileEducationDTO')
    projects = fields.Nested('CandidateProfileProjectsDTO')
    social_presence = fields.Nested('CandidateProfileSocialPresenceDTO')


class CandidateProfileTechnicalSkillsDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    match_id = fields.Str(required=True)
    score = fields.Float(required=True)
    skill_matches = fields.Nested('CandidateProfileTechnicalSkillMatchDTO', many=True)
    frameworks = fields.Nested('CandidateProfileFrameworkToolDTO', many=True)


class CandidateProfileTechnicalSkillMatchDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    technical_skills_id = fields.Str(required=True)
    skill = fields.Str(required=True)
    job_relevance = fields.Float(required=True)
    candidate_proficiency = fields.Float(required=True)


class CandidateProfileFrameworkToolDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    technical_skills_id = fields.Str(required=True)
    name = fields.Str(required=True)
    proficiency = fields.Float(required=True)


class CandidateProfileSoftSkillsDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    match_id = fields.Str(required=True)
    score = fields.Float(required=True)
    skill_matches = fields.Nested('CandidateProfileSoftSkillMatchDTO', many=True)


class CandidateProfileSoftSkillMatchDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    soft_skills_id = fields.Str(required=True)
    skill = fields.Str(required=True)
    proficiency = fields.Float(required=True)


class CandidateProfileExperienceDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    match_id = fields.Str(required=True)
    score = fields.Float(required=True)
    years_of_experience = fields.Float(required=True)
    industry_experiences = fields.Nested('CandidateProfileIndustryExperienceDTO', many=True)
    relevant_roles = fields.Nested('CandidateProfileRelevantRoleDTO', many=True)


class CandidateProfileIndustryExperienceDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    experience_id = fields.Str(required=True)
    industry = fields.Str(required=True)
    years = fields.Float(required=True)


class CandidateProfileRelevantRoleDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    experience_id = fields.Str(required=True)
    title = fields.Str(required=True)
    company = fields.Str(required=True)
    duration = fields.Float(required=True)


class CandidateProfileEducationDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    match_id = fields.Str(required=True)
    score = fields.Float(required=True)
    degrees = fields.Nested('CandidateProfileDegreeDTO', many=True)


class CandidateProfileDegreeDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    education_id = fields.Str(required=True)
    degree = fields.Str(required=True)
    major = fields.Str(required=True)
    institution = fields.Str(required=True)


class CandidateProfileProjectsDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    match_id = fields.Str(required=True)
    score = fields.Float(required=True)
    items = fields.Nested('CandidateProfileProjectDTO', many=True)


class CandidateProfileProjectDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    projects_id = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    relevance = fields.Float(required=True)


class CandidateProfileSocialPresenceDTO(CamelCaseSchema):
    id = fields.Str(dump_only=True)
    match_id = fields.Str(required=True)
    score = fields.Float(required=True)
    linkedin_activity_score = fields.Float(required=True)
    github_contribution_score = fields.Float(required=True)
    blog_post_score = fields.Float(required=True)