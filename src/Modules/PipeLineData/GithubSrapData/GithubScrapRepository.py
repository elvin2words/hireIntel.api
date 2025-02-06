from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from src.Helpers.BaseRepository import BaseRepository
from src.Modules.PipeLineData.GithubSrapData.GithubScrapModels import GitHubProfile, GithubRepository

class GitHubProfileRepository(BaseRepository[GitHubProfile]):
    def __init__(self):
        super().__init__(GitHubProfile)

    def get_by_candidate_id(self, candidate_id: str) -> Optional[GitHubProfile]:
        try:
            return self._db.session.query(self._model).filter_by(candidate_id=candidate_id).first()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e

class GithubRepositoryRepository(BaseRepository[GithubRepository]):
    def __init__(self):
        super().__init__(GithubRepository)

    def get_by_profile_id(self, profile_id: str) -> List[GithubRepository]:
        try:
            return self._db.session.query(self._model).filter_by(github_profile_id=profile_id).all()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            raise e