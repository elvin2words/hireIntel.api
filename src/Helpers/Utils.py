import re

from flask_jwt_extended import get_jwt_identity
from marshmallow import Schema, post_dump

from src.Modules.Auth.AuthModels import Role



class InternalDTOUser:
    def __init__(self, user_id, email, role):
        global role_map
        if isinstance(role, str):
            role_map = {
                "user": Role.USER,
                "admin": Role.ADMIN,
            }

        self.user_id = user_id
        self.email = email
        self.role = role_map.get(role.lower())


def getLoggedUser():
    identity = get_jwt_identity()
    user_id = identity['user_id']
    email = identity['email']
    role = identity['role']
    return InternalDTOUser(user_id=user_id, email=email, role=role)


def toCamelCase(snake_str):
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class CamelCaseSchema(Schema):
    """Base schema that converts snake_case to camelCase"""

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = toCamelCase(field_name)

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}

def camelToSnake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def updateObject(target_obj, source_obj):
    """
    updated properties in target_obj with values from source_obj
    :param target_obj: the object to be updated: type model
    :param source_obj: the object with the updated content: type dict
    :return: target_obj
    """
    for key, value in source_obj.items():
        snake_case_key = camelToSnake(key)
        if hasattr(target_obj, snake_case_key):
            setattr(target_obj, snake_case_key, value)
    return target_obj