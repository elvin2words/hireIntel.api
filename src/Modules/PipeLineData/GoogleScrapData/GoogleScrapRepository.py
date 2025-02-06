from src.Helpers.BaseRepository import BaseRepository
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapModels import CandidateProfessionalHandle, CandidateCrime, \
    HandleType


class CandidateProfessionalHandleRepository(BaseRepository[CandidateProfessionalHandle]):
    def __init__(self):
        super().__init__(CandidateProfessionalHandle)

    def getLinkedInHandleByCandidateId(self, candidate_id):
        return self._db.session.query(CandidateProfessionalHandle).filter_by(
            candidate_id=candidate_id,
            handle_type=HandleType.LINKED_IN
        ).first()

    def getGitHubHandleByCandidateId(self, candidate_id):
        return self._db.session.query(CandidateProfessionalHandle).filter_by(
            candidate_id=candidate_id,
            handle_type=HandleType.GITHUB
        ).first()

class CandidateCrimeRepository(BaseRepository[CandidateCrime]):
    def __init__(self):
        super().__init__(CandidateCrime)