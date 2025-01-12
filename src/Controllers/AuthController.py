from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.Helpers.Response import apiResponse
from src.Helpers.Utils import getLoggedUser
from src.Modules.Auth.AuthModels import Role
from src.Modules.Auth.AuthService import AuthService

AUTH_CONTROLLER = Blueprint('user_controller', __name__, url_prefix='/api/v1/auth')
authService = AuthService()


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


def extract_token():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(" ")[1]
    return token


@AUTH_CONTROLLER.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print("my data: ", data)
    tokens = authService.register(data)
    return apiResponse(False, 201,tokens, "User created successfully")


@AUTH_CONTROLLER.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    tokens = authService.login(data['email'], data['password'])
    return apiResponse(False, 201,tokens, "Login successful")


@AUTH_CONTROLLER.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user = getLoggedUser()
    authService.logout(user.user_id)
    return apiResponse(False, 200, None, "Logout successful")


@AUTH_CONTROLLER.route('/refresh/tokens', methods=['POST'])
@jwt_required(refresh=True)
def request_access_token():
    identity = get_jwt_identity()
    user = getLoggedUser()
    token = extract_token()
    tokens = authService.renew_access_token(token, user)
    return apiResponse(False, 201,tokens, "Tokens have been refreshed successfully")


@AUTH_CONTROLLER.route('/user/fetch', methods=['GET'])
@jwt_required()
def get_user_credentials():
    user = getLoggedUser()
    user_data = authService.fetch_by_user_id(user.user_id)
    return  apiResponse(False, 200, user_data, "User credentials fetched successfully")

@AUTH_CONTROLLER.route('/user/delete/<string:user_id>', methods=['DELETE'])
@jwt_required()
def remove_user(user_id: str):
    user_dto = authService.remove_user(user_id)
    return  apiResponse(False, 200, user_dto, "User removed successfully")


@AUTH_CONTROLLER.route('/user/update', methods=['PUT'])
@jwt_required()
def update_user_credentials():
    user = getLoggedUser()
    data = request.get_json()
    user_dto = authService.update_user_credentials(data, user.user_id)
    return apiResponse(False, 200, user_dto, "User credentials updated successfully")


@AUTH_CONTROLLER.route('/user/admin/fetch/all', methods=['GET'])
@jwt_required()
def fetch_all_admin_users():
    users_dto = authService.fetch_all_admin_user()
    return apiResponse(False, 200, users_dto, "Admin users fetched successfully")
