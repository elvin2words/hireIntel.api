from typing import Optional, List
from src.Helpers.BaseRepository import BaseRepository
from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationModels import (
    CandidateProfile,
    CandidateProfileMatch,
    CandidateProfileTechnicalSkills,
    CandidateProfileTechnicalSkillMatch,
    CandidateProfileFrameworkAndTool,
    CandidateProfileSoftSkills,
    CandidateProfileSoftSkillMatch,
    CandidateProfileExperience,
    CandidateProfileIndustryExperience,
    CandidateProfileRelevantRole,
    CandidateProfileEducation,
    CandidateProfileDegree,
    CandidateProfileProjectsAndAchievements,
    CandidateProfileProject,
    CandidateProfileSocialPresence
)


class CandidateProfileRepository(BaseRepository[CandidateProfile]):
    def __init__(self):
        super().__init__(CandidateProfile)

    def get_by_candidate_id(self, candidate_id: str) -> Optional[CandidateProfile]:
        return self._model.query.filter_by(candidate_id=candidate_id).first()


class CandidateProfileMatchRepository(BaseRepository[CandidateProfileMatch]):
    def __init__(self):
        super().__init__(CandidateProfileMatch)

    def get_by_profile_id(self, profile_id: str) -> List[CandidateProfileMatch]:
        return self._model.query.filter_by(profile_id=profile_id).all()

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileMatch]:
        return self._model.query.filter_by(id=match_id).first()


class TechnicalSkillsRepository(BaseRepository[CandidateProfileTechnicalSkills]):
    def __init__(self):
        super().__init__(CandidateProfileTechnicalSkills)

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileTechnicalSkills]:
        return self._model.query.filter_by(match_id=match_id).first()


class TechnicalSkillMatchRepository(BaseRepository[CandidateProfileTechnicalSkillMatch]):
    def __init__(self):
        super().__init__(CandidateProfileTechnicalSkillMatch)

    def get_by_technical_skills_id(self, technical_skills_id: str) -> List[CandidateProfileTechnicalSkillMatch]:
        return self._model.query.filter_by(technical_skills_id=technical_skills_id).all()


class FrameworkToolRepository(BaseRepository[CandidateProfileFrameworkAndTool]):
    def __init__(self):
        super().__init__(CandidateProfileFrameworkAndTool)

    def get_by_technical_skills_id(self, technical_skills_id: str) -> List[CandidateProfileFrameworkAndTool]:
        return self._model.query.filter_by(technical_skills_id=technical_skills_id).all()


class SoftSkillsRepository(BaseRepository[CandidateProfileSoftSkills]):
    def __init__(self):
        super().__init__(CandidateProfileSoftSkills)

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileSoftSkills]:
        return self._model.query.filter_by(match_id=match_id).first()


class SoftSkillMatchRepository(BaseRepository[CandidateProfileSoftSkillMatch]):
    def __init__(self):
        super().__init__(CandidateProfileSoftSkillMatch)

    def get_by_soft_skills_id(self, soft_skills_id: str) -> List[CandidateProfileSoftSkillMatch]:
        return self._model.query.filter_by(soft_skills_id=soft_skills_id).all()


class ExperienceRepository(BaseRepository[CandidateProfileExperience]):
    def __init__(self):
        super().__init__(CandidateProfileExperience)

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileExperience]:
        return self._model.query.filter_by(match_id=match_id).first()


class IndustryExperienceRepository(BaseRepository[CandidateProfileIndustryExperience]):
    def __init__(self):
        super().__init__(CandidateProfileIndustryExperience)

    def get_by_experience_id(self, experience_id: str) -> List[CandidateProfileIndustryExperience]:
        return self._model.query.filter_by(experience_id=experience_id).all()


class RelevantRoleRepository(BaseRepository[CandidateProfileRelevantRole]):
    def __init__(self):
        super().__init__(CandidateProfileRelevantRole)

    def get_by_experience_id(self, experience_id: str) -> List[CandidateProfileRelevantRole]:
        return self._model.query.filter_by(experience_id=experience_id).all()


class EducationRepository(BaseRepository[CandidateProfileEducation]):
    def __init__(self):
        super().__init__(CandidateProfileEducation)

    def get_by_candidate_id(self, candidate_id: str) -> List[CandidateProfileEducation]:
        return self._model.query.join(CandidateProfileMatch).filter(
            CandidateProfileMatch.candidate_id == candidate_id).all()

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileEducation]:
        return self._model.query.filter_by(match_id=match_id).first()


class DegreeRepository(BaseRepository[CandidateProfileDegree]):
    def __init__(self):
        super().__init__(CandidateProfileDegree)

    def get_by_education_id(self, education_id: str) -> List[CandidateProfileDegree]:
        return self._model.query.filter_by(education_id=education_id).all()


class ProjectsRepository(BaseRepository[CandidateProfileProjectsAndAchievements]):
    def __init__(self):
        super().__init__(CandidateProfileProjectsAndAchievements)

    def get_by_candidate_id(self, candidate_id: str) -> List[CandidateProfileProjectsAndAchievements]:
        return self._model.query.join(CandidateProfileMatch).filter(
            CandidateProfileMatch.candidate_id == candidate_id).all()

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileProjectsAndAchievements]:
        return self._model.query.filter_by(match_id=match_id).first()


class ProjectRepository(BaseRepository[CandidateProfileProject]):
    def __init__(self):
        super().__init__(CandidateProfileProject)

    def get_by_projects_id(self, projects_id: str) -> List[CandidateProfileProject]:
        return self._model.query.filter_by(projects_id=projects_id).all()


class SocialPresenceRepository(BaseRepository[CandidateProfileSocialPresence]):
    def __init__(self):
        super().__init__(CandidateProfileSocialPresence)

    def get_by_candidate_id(self, candidate_id: str) -> List[CandidateProfileSocialPresence]:
        return self._model.query.join(CandidateProfileMatch).filter(
            CandidateProfileMatch.candidate_id == candidate_id).all()

    def get_by_match_id(self, match_id: str) -> Optional[CandidateProfileSocialPresence]:
        return self._model.query.filter_by(match_id=match_id).first()