import datetime
import uuid
from src.Modules.Auth.AuthDTOs import UserDTO, TokenDTO
from src.Modules.Auth.AuthModels import TokenType, Token, User, Role, Profile
from src.Helpers.Validators import validateUserData
from flask_jwt_extended import create_access_token, create_refresh_token
from src.Helpers.ErrorHandling import CustomError, handleCustomError
from src.Modules.Auth.AuthRepository import AuthRepository

from src.Helpers.Utils import updateObject
from werkzeug.security import generate_password_hash, check_password_hash


class AuthService:
    def __init__(self):
        self.__auth_repository = AuthRepository()

    def __create_access_refresh_tokens(self, user):
        refresh_token_expiration = datetime.timedelta(days=7)
        access_token_expiration = datetime.timedelta(hours=24)
        # Create tokens
        access_token = Token(
            token_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token=create_access_token(identity={
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role.value,
            }, expires_delta=access_token_expiration),  # Todo: configure token expiry date
            token_type=TokenType.ACCESS,
            is_expired=False,
            is_revoked=False,
            created_at=datetime.datetime.utcnow()
        )

        refresh_token = Token(
            token_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token=create_refresh_token(identity={
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role.value,
            }, expires_delta=refresh_token_expiration),  # Todo: configure token expiry date
            token_type=TokenType.REFRESH,
            is_expired=False,
            is_revoked=False,
            created_at=datetime.datetime.utcnow()
        )

        # Save tokens
        self.__auth_repository.save_token(access_token)
        self.__auth_repository.save_token(refresh_token)

        # Return tokens
        return access_token, refresh_token

    def register(self, data):
        try:
            validateUserData(data)
            user = User(
                user_id=str(uuid.uuid4()),  # Generate unique ID
                email=data['email'],
                password=generate_password_hash(
                    data['password'], salt_length=16),
                first_name=data['firstName'],
                last_name=data['lastName'],
                role=Role[data['role']]
            )

            # Check if user exists
            db_user = self.__auth_repository.fetch_user_by_email(user.email)

            if db_user:
                raise Exception("User email already exists")

            self.__auth_repository.save_user(user)
            # Create and save user profile
            profile = Profile(
                profile_id=str(uuid.uuid4()),
                user_id=user.user_id,
                sex="",
                nationality="",
                profession="",
                address="",
                city="",
                postal_code="",
                country="",
                about_me=""
            )

            access_token, refresh_token = self.__create_access_refresh_tokens(user)
            # Save token in database
            return {"accessToken": access_token.token, "refreshToken": refresh_token.token}

        except CustomError as e:
            raise handleCustomError(e)

    def login(self, email, password):

        try:
            user = self.__auth_repository.fetch_user_by_email(email)
            if not user or not check_password_hash(user.password, password):
                raise Exception("Invalid credentials", 401)

            # Revoke all user tokens
            self.__auth_repository.expire_all_tokens_by_user_id(user.user_id)
            self.__auth_repository.revoke_all_tokens_by_user_id(user.user_id)

            # Create and save tokens
            access_token, refresh_token = self.__create_access_refresh_tokens(user)
        except CustomError as e:
            raise handleCustomError(e)

        # Save tokens in database
        return {"accessToken": access_token.token, "refreshToken": refresh_token.token}

    def logout(self, user_id):
        try:
            user = self.__auth_repository.fetch_user_by_id(user_id)
        except CustomError as e:
            raise Exception(e)
            # raise handle_custom_error(e)

        try:
            # Revoke all user tokens
            self.__auth_repository.expire_all_tokens_by_user_id(user.user_id)
            self.__auth_repository.revoke_all_tokens_by_user_id(user.user_id)
        except CustomError as e:
            raise Exception(e)
            # raise handle_custom_error(e)

    def renew_access_token(self, token, user):
        try:
            # Confirm token exist and is not revoked or expired
            db_token = self.__auth_repository.fetch_by_token(token)

            # Todo: make it able to use CustomError exception
            if db_token:
                if db_token.token_type != TokenType.REFRESH:
                    # raise CustomError("Token type invalid, pass a refresh token", 401)
                    raise Exception("Token type invalid, pass a refresh token")
                if db_token.is_expired or db_token.is_revoked:
                    # raise CustomError("Token has been revoked or expired", 401)
                    raise Exception("Token has been revoked or expired")

                # Revoke all user tokens
                self.__auth_repository.expire_all_tokens_by_user_id(user.user_id)
                self.__auth_repository.revoke_all_tokens_by_user_id(user.user_id)

                # Create and save new tokens
                access_token, refresh_token = self.__create_access_refresh_tokens(user)

                # return the new tokens
                return {"accessToken": access_token.token, "refreshToken": refresh_token.token}
            else:
                raise CustomError("Token not found", 404)

        except CustomError as e:
            raise handleCustomError(e)

    def fetch_by_user_id(self, user_id):
        try:
            db_user = self.__auth_repository.fetch_user_by_id(user_id)

            if db_user is None:
                raise Exception("User does not exist")

            # Logging user attributes
            print("User attributes:", db_user.user_id, db_user.first_name, db_user.last_name, db_user.email,
                  db_user.role)

            # Dump user data into DTO and check for issues here
            return UserDTO().dump(db_user)

        except CustomError as e:
            raise handleCustomError(e)
        except AttributeError as e:
            print("Attribute error:", str(e))  # Add detailed error logging
            raise Exception("An attribute error occurred while processing the user data.")

    def update_user_credentials(self, data, user_id):
        try:
            db_user = self.__auth_repository.fetch_user_by_id(user_id)
            if db_user is None:
                raise Exception("User does not exist")

            # Update the user credentials
            updated_user = updateObject(db_user, data)
            self.__auth_repository.update_user()

            return UserDTO().dump(updated_user)
        except CustomError as e:
            raise handleCustomError(e)



    """
    Token Methods
    """


    def fetch_token_by_id(self, token_id):
        try:
            token = self.__auth_repository.fetch_token_by_id(token_id)
            return TokenDTO(many=False).dump(token)
        except Exception as e:
            raise CustomError(str(e), 400)

    def save_token(self, token):
        try:
            self.__auth_repository.save_token(token)
            return TokenDTO(many=False).dump(token)
        except Exception as e:
            raise CustomError(str(e), 400)


    def fetch_valid_tokens_for_user(self, user_id):
        try:
            tokens = self.__auth_repository.fetch_valid_tokens_by_user_id(user_id)
            return TokenDTO(many=True).dump(tokens)
        except Exception as e:
            raise CustomError(str(e), 400)

    def revoke_token_by_id(self, token_id):
        try:
            self.__auth_repository.revoke_token_by_id(token_id)
        except Exception as e:
            raise CustomError(str(e), 400)

    def expire_token_by_id(self, token_id):
        try:
            self.__auth_repository.expire_token_by_id(token_id)
        except Exception as e:
            raise CustomError(str(e), 400)

    def revoke_all_tokens_for_user(self, user_id):
        try:
            self.__auth_repository.revoke_all_tokens_by_user_id(user_id)
        except Exception as e:
            raise CustomError(str(e), 400)

    def expire_all_tokens_for_user(self, user_id):
        try:
            self.__auth_repository.expire_all_tokens_by_user_id(user_id)
        except Exception as e:
            raise CustomError(str(e), 400)

    def fetch_all_admin_user(self):
        try:
            return UserDTO(many=True).dump(self.__auth_repository.fetch_all_admin_user())
        except Exception as e:
            raise CustomError(str(e), 400)

    def remove_user(self, user_id):
        try:
            user = self.__auth_repository.fetch_user_by_id(user_id)
            self.__auth_repository.remove_user(user_id)
            return UserDTO(many=False).dump(user)
        except Exception as e:
            raise CustomError(str(e), 400)

    def initialize_admin_user(self, admin_email, admin_password):
        try:
            # Check if an admin user already exists
            admin_user = self.__auth_repository.fetch_user_by_email(admin_email)
            if admin_user:
                print(f"Admin user with email {admin_email} already exists.")
                return {"message": "Admin user already exists.", "admin_email": admin_email}

            # Create the admin user
            admin_user = User(
                user_id=str(uuid.uuid4()),  # Generate unique ID
                email=admin_email,
                password=generate_password_hash(admin_password, salt_length=16),
                first_name="Admin",
                last_name="User",
                role=Role.ADMIN  # Assuming Role.ADMIN is defined
            )

            # Save admin user to the database
            self.__auth_repository.save_user(admin_user)

            print(f"Admin user with email {admin_email} created successfully.")
            return {"message": "Admin user created successfully.", "admin_email": admin_email}

        except Exception as e:
            raise Exception(f"Failed to initialize admin user: {str(e)}")
