from marshmallow import ValidationError


def validateUserData(data):
    if 'email' not in data or not data['email']:
        raise ValidationError("Email is required")
    if 'password' not in data or not data['password']:
        raise ValidationError("password is required")
    if 'role' not in data or not data['role']:
        raise ValidationError("Role is required")
