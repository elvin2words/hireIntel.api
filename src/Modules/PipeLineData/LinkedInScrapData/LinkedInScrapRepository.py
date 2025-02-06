from src.Helpers.BaseRepository import BaseRepository
from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapModels import LinkedInProfile, LinkedInWorkExperience, LinkedInEducation

class LinkedInProfileRepository(BaseRepository[LinkedInProfile]):
    def __init__(self):
        super().__init__(LinkedInProfile)

    def get_by_candidate_id(self, candidate_id: str) -> LinkedInProfile:
        return self._db.session.query(self._model).filter_by(candidate_id=candidate_id).first()

class LinkedInWorkExperienceRepository(BaseRepository[LinkedInWorkExperience]):
    def __init__(self):
        super().__init__(LinkedInWorkExperience)

class LinkedInEducationRepository(BaseRepository[LinkedInEducation]):
    def __init__(self):
        super().__init__(LinkedInEducation)