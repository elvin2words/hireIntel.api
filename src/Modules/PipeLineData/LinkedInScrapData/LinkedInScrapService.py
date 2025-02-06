from typing import Optional

from src.Helpers.ErrorHandling import CustomError
from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapDTOs import LinkedInProfileDTO, LinkedInWorkExperienceDTO, LinkedInEducationDTO
from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapModels import LinkedInProfile, LinkedInWorkExperience, LinkedInEducation
from src.Modules.PipeLineData.LinkedInScrapData.LinkedInScrapRepository import LinkedInProfileRepository, LinkedInWorkExperienceRepository, LinkedInEducationRepository

class LinkedInScrapDataService:
    def __init__(self):
        self.__linkedInProfileRepository = LinkedInProfileRepository()
        self.__linkedInWorkExperienceRepository = LinkedInWorkExperienceRepository()
        self.__linkedInEducationRepository = LinkedInEducationRepository()

    def save_profile(self,candidate_id, profile_data):
        try:
            print("the data : ", profile_data)
            profile = LinkedInProfile(
                candidate_id=candidate_id,
                username=profile_data['basic_info']['username'],
                full_name=profile_data['basic_info']['full_name'],
                headline=profile_data['basic_info']['headline'],
                location=profile_data['basic_info']['location'],
                summary=profile_data['basic_info']['summary']
            )
            saved_profile = self.__linkedInProfileRepository.create(profile)

            for exp_data in profile_data['experience']:
                experience = LinkedInWorkExperience(
                    linked_in_profile_id=saved_profile.id,
                    company=exp_data['company'],
                    title=exp_data['title'],
                    location=exp_data['location'],
                    duration=exp_data['duration'],
                    description=exp_data['description']
                )
                self.__linkedInWorkExperienceRepository.create(experience)

            for edu_data in profile_data['education']:
                education = LinkedInEducation(
                    linked_in_profile_id=saved_profile.id,
                    school=edu_data['school'],
                    degree=edu_data['degree'],
                    field=edu_data['field'],
                    years=edu_data['years']
                )
                self.__linkedInEducationRepository.create(education)

            saved_profile.skills = profile_data['skills']
            self.__linkedInProfileRepository.update(saved_profile)

            return LinkedInProfileDTO().dump(saved_profile)
        except Exception as e:
            raise CustomError(str(e), 400)

    def get_profile_by_candidate_id(self, candidate_id: str) -> Optional[dict]:
        try:
            profile = self.__linkedInProfileRepository.get_by_candidate_id(candidate_id)
            if profile:
                profile_data = LinkedInProfileDTO().dump(profile)
                profile_data['experience'] = LinkedInWorkExperienceDTO(many=True).dump(profile.experience)
                profile_data['education'] = LinkedInEducationDTO(many=True).dump(profile.education)
                return profile_data
            return None
        except Exception as e:
            raise CustomError(str(e), 400)