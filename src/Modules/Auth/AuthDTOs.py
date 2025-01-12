from marshmallow import  fields, validate, post_dump

from src.Helpers.Utils import CamelCaseSchema


class UserDTO(CamelCaseSchema):
    user_id = fields.Str(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    role = fields.Method("get_role")
    created_at = fields.DateTime(dump_only=True)

    def get_role(self, obj):
        return obj.role.value if hasattr(obj.role, 'value') else str(obj.role)

    @post_dump
    def format_role(self, data, **kwargs):
        if 'role' in data and data['role'].startswith("Role."):
            data['role'] = data['role'].replace("Role.", "")
        return data


class ProfileDTO(CamelCaseSchema):
    profile_id = fields.Str(dump_only=True)
    user_id = fields.Str(required=True)
    sex = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    nationality = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    profession = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    address = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    city = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    postal_code = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    country = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    about_me = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    created_at = fields.DateTime(dump_only=True)



# New DTOs for remaining models
class TokenDTO(CamelCaseSchema):
    token_id = fields.Str(dump_only=True)
    user_id = fields.Str(required=True)
    token = fields.Str(dump_only=True)
    token_type = fields.Method("get_token_type")
    is_expired = fields.Bool(dump_only=True)
    is_revoked = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    def get_token_type(self, obj):
        return obj.token_type.value if hasattr(obj.token_type, 'value') else str(obj.token_type)

