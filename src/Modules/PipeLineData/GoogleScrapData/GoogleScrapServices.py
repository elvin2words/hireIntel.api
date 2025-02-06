from src.Helpers.ErrorHandling import CustomError
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapDTOs import CandidateProfessionalHandleDTO
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapModels import CandidateProfessionalHandle, HandleType
from src.Modules.PipeLineData.GoogleScrapData.GoogleScrapRepository import CandidateProfessionalHandleRepository, \
    CandidateCrimeRepository
from src.PipeLines.Profiling.DataScraping.GoogleScrap.SerperGoogleScraper import Profile


class GoogleScrapDataService:
    def __init__(self):
        self.__candidateProfessionalHandleRepository = CandidateProfessionalHandleRepository()
        self.__candidateCrimeRepository = CandidateCrimeRepository()

    def saveCandidateHandles(self, candidate_id, profile: Profile):
        try:
            handles = []

            if profile.githubHandle.verified:
                githubHandle = CandidateProfessionalHandle(
                    candidate_id=candidate_id,
                    handle=profile.githubHandle.github_username,
                    handle_type=HandleType.GITHUB,
                    handle_url=profile.githubHandle.github_url,
                    verified=profile.githubHandle.verified,
                )
                handles.append(self.__candidateProfessionalHandleRepository.create(githubHandle))

            if profile.linkedInHandle.verified:
                linkedInHandle = CandidateProfessionalHandle(
                    candidate_id=candidate_id,
                    handle=profile.linkedInHandle.linkedin_username,
                    handle_type=HandleType.LINKED_IN,
                    handle_url=profile.linkedInHandle.linkedin_url,
                    verified=profile.linkedInHandle.verified,
                )
                handles.append(self.__candidateProfessionalHandleRepository.create(linkedInHandle))

            return CandidateProfessionalHandleDTO(many=True).dump(handles) if handles else None
        except Exception as e:
            raise CustomError(str(e), 400)

    def getLinkedInHandle(self, candidate_id):
        try:
            handle = self.__candidateProfessionalHandleRepository.getLinkedInHandleByCandidateId(candidate_id)

            if not handle:
                raise Exception("No linkedin handle found")
            return CandidateProfessionalHandleDTO(many=False).dump(handle)
        except Exception as e:
            raise CustomError(str(e), 400)

    def getGitHubHandle(self, candidate_id):
        try:
            handle = self.__candidateProfessionalHandleRepository.getGitHubHandleByCandidateId(candidate_id)

            if not handle:
                raise Exception("No github handle found")
            return CandidateProfessionalHandleDTO(many=False).dump(handle)
        except Exception as e:
            raise CustomError(str(e), 400)