from datetime import datetime

from src.config.DBModelsConfig import db
from src.Modules.Auth.AuthModels import Profile, User, Token, Role


class AuthRepository:
    def __init__(self):
        self.db = db

    """
    Authentication Methods
    """
    def save_user(self, user):
        self.db.session.add(user)
        self.db.session.commit()

    def fetch_user_by_email(self, email):
        return self.db.session.query(User).filter_by(email=email).first()

    def fetch_user_by_id(self, user_id):
        return self.db.session.query(User).filter_by(user_id=user_id).first()

    def update_user(self):
        self.db.session.commit()



    """
    Token Methods
    """

    def save_token(self, token):
        self.db.session.add(token)
        self.db.session.commit()

    def fetch_token_by_user_id(self, user_id):
        return self.db.session.query(Token).filter_by(user_id=user_id).all()


    def fetch_token_by_id(self, token_id):
        return self.db.session.query(Token).filter_by(token_id=token_id).first()

    def fetch_valid_tokens_by_user_id(self, user_id):
        current_time = datetime.utcnow()
        return self.db.session.query(Token).filter(
            Token.user_id == user_id,
            Token.revoked == False,
            Token.expiry_date > current_time
        ).all()

    def revoke_token_by_id(self, token_id):
        token = self.db.session.query(Token).filter_by(token_id=token_id).first()
        if token:
            token.revoked = True
            self.db.session.commit()

    def expire_token_by_id(self, token_id):
        token = self.db.session.query(Token).filter_by(token_id=token_id).first()
        if token:
            token.expiry_date = datetime.utcnow()
            self.db.session.commit()

    def revoke_all_tokens_by_user_id(self, user_id):
        tokens = self.db.session.query(Token).filter_by(user_id=user_id).all()
        for token in tokens:
            token.revoked = True
        self.db.session.commit()

    def expire_all_tokens_by_user_id(self, user_id):
        tokens = self.db.session.query(Token).filter_by(user_id=user_id).all()
        current_time = datetime.utcnow()
        for token in tokens:
            token.expiry_date = current_time
        self.db.session.commit()

    def revoke_token_by_user_id(self, user_id):
        token = self.db.session.query(Token).filter_by(user_id=user_id).first()
        if token:
            token.revoked = True
            self.db.session.commit()

    def expire_token_by_user_id(self, user_id):
        token = self.db.session.query(Token).filter_by(user_id=user_id).first

    def fetch_by_token(self, token):
        return self.db.session.query(Token).filter_by(token=token).first()

    def fetch_all_tokens(self):
        pass

    def delete_token(self, token_id):
        pass

    def update_token(self, token):
        pass

    def fetch_all_admin_user(self):
        return self.db.session.query(User).filter_by(
            role="ADMIN"
        ).all()

    def remove_user(self, user_id):
        user = self.fetch_user_by_id(user_id)
        self.db.session.delete(user)
        self.db.session.commit()

