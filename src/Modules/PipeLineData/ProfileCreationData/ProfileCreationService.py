from datetime import datetime
from typing import Optional, List
from src.Helpers.ErrorHandling import CustomError
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
from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationDTOs import (
   CandidateProfileDTO,
   CandidateProfileMatchDTO,
   CandidateProfileTechnicalSkillsDTO,
   CandidateProfileTechnicalSkillMatchDTO,
   CandidateProfileFrameworkToolDTO,
   CandidateProfileSoftSkillsDTO,
   CandidateProfileSoftSkillMatchDTO,
   CandidateProfileExperienceDTO,
   CandidateProfileIndustryExperienceDTO,
   CandidateProfileRelevantRoleDTO,
   CandidateProfileEducationDTO,
   CandidateProfileDegreeDTO,
   CandidateProfileProjectsDTO,
   CandidateProfileProjectDTO,
   CandidateProfileSocialPresenceDTO
)
from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationRepository import (
    CandidateProfileRepository,
    CandidateProfileMatchRepository,
    TechnicalSkillsRepository,
    SoftSkillsRepository,
    ExperienceRepository,
    EducationRepository,
    ProjectsRepository,
    SocialPresenceRepository, TechnicalSkillMatchRepository, FrameworkToolRepository, SoftSkillMatchRepository,
    IndustryExperienceRepository, RelevantRoleRepository, DegreeRepository, ProjectRepository
)

class CandidateProfileDataService:
   def __init__(self):
       self.__profileRepo = CandidateProfileRepository()
       self.__matchRepo = CandidateProfileMatchRepository()
       self.__technicalSkillsRepo = TechnicalSkillsRepository()
       self.__technicalSkillMatchRepo = TechnicalSkillMatchRepository()
       self.__frameworkToolRepo = FrameworkToolRepository()
       self.__softSkillsRepo = SoftSkillsRepository()
       self.__softSkillMatchRepo = SoftSkillMatchRepository()
       self.__experienceRepo = ExperienceRepository()
       self.__industryExpRepo = IndustryExperienceRepository()
       self.__relevantRoleRepo = RelevantRoleRepository()
       self.__educationRepo = EducationRepository()
       self.__degreeRepo = DegreeRepository()
       self.__projectsRepo = ProjectsRepository()
       self.__projectRepo = ProjectRepository()
       self.__socialPresenceRepo = SocialPresenceRepository()

   def save_profile(self, candidate_id: str, job_id: str,  profile_data: dict) -> dict:
       try:
           # Create profile
           profile = CandidateProfile(candidate_id=candidate_id)
           saved_profile = self.__profileRepo.create(profile)

           # Create match
           match = CandidateProfileMatch(
               profile_id=saved_profile.id,
               job_id=job_id,
               overall_match_score=float(profile_data['overallMatch']['score']),
               overall_match_details=profile_data['overallMatch']['details'],
               diversity=bool(profile_data.get('diversity', False))
           )
           saved_match = self.__matchRepo.create(match)

           # Technical Skills
           tech_skills = CandidateProfileTechnicalSkills(
               match_id=saved_match.id,
               score=float(profile_data['technicalSkills']['score'])
           )
           saved_tech = self.__technicalSkillsRepo.create(tech_skills)

           for skill in profile_data['technicalSkills']['skillMatches']:
               tech_match = CandidateProfileTechnicalSkillMatch(
                   technical_skills_id=saved_tech.id,
                   skill=skill['skill'],
                   job_relevance=float(skill['jobRelevance']),
                   candidate_proficiency=float(skill['candidateProficiency'])
               )
               self.__technicalSkillMatchRepo.create(tech_match)

           for framework in profile_data['technicalSkills']['frameworksAndTools']:
               tool = CandidateProfileFrameworkAndTool(
                   technical_skills_id=saved_tech.id,
                   name=framework['name'],
                   proficiency=float(framework['proficiency'])
               )
               self.__frameworkToolRepo.create(tool)

           # Soft Skills
           soft_skills = CandidateProfileSoftSkills(
               match_id=saved_match.id,
               score=float(profile_data['softSkills']['score'])
           )
           saved_soft = self.__softSkillsRepo.create(soft_skills)

           for skill in profile_data['softSkills']['skillMatches']:
               soft_match = CandidateProfileSoftSkillMatch(
                   soft_skills_id=saved_soft.id,
                   skill=skill['skill'],
                   proficiency=float(skill['proficiency'])
               )
               self.__softSkillMatchRepo.create(soft_match)

           # Experience
           experience = CandidateProfileExperience(
               match_id=saved_match.id,
               score=float(profile_data['experience']['score']),
               years_of_experience=float(profile_data['experience']['yearsOfExperience'])
           )
           saved_exp = self.__experienceRepo.create(experience)

           for industry in profile_data['experience']['industryExperience']:
               ind_exp = CandidateProfileIndustryExperience(
                   experience_id=saved_exp.id,
                   industry=industry['industry'],
                   years=float(industry['years'])
               )
               self.__industryExpRepo.create(ind_exp)

           for role in profile_data['experience']['relevantRoles']:
               rel_role = CandidateProfileRelevantRole(
                   experience_id=saved_exp.id,
                   title=role['title'],
                   company=role['company'],
                   duration=float(role['duration'])
               )
               self.__relevantRoleRepo.create(rel_role)

           # Education
           education = CandidateProfileEducation(
               match_id=saved_match.id,
               score=float(profile_data['education']['score'])
           )
           saved_edu = self.__educationRepo.create(education)

           for degree in profile_data['education']['degrees']:
               deg = CandidateProfileDegree(
                   education_id=saved_edu.id,
                   degree=degree['degree'],
                   major=degree['major'],
                   institution=degree['institution']
               )
               self.__degreeRepo.create(deg)

           # Projects
           projects = CandidateProfileProjectsAndAchievements(
               match_id=saved_match.id,
               score=float(profile_data['projectsAndAchievements']['score'])
           )
           saved_proj = self.__projectsRepo.create(projects)

           for item in profile_data['projectsAndAchievements']['items']:
               project = CandidateProfileProject(
                   projects_id=saved_proj.id,
                   name=item['name'],
                   description=item['description'],
                   relevance=float(item['relevance'])
               )
               self.__projectRepo.create(project)

           # Social Presence
           social = CandidateProfileSocialPresence(
               match_id=saved_match.id,
               score=float(profile_data['socialPresence']['score']),
               linkedin_activity_score=float(profile_data['socialPresence']['linkedInActivityScore']),
               github_contribution_score=float(profile_data['socialPresence']['githubContributionScore']),
               blog_post_score=float(profile_data['socialPresence']['blogPostScore'])
           )
           self.__socialPresenceRepo.create(social)

           return self.get_profile_by_candidate_id(candidate_id)

       except Exception as e:
           raise CustomError(str(e), 400)

   def get_profile_by_candidate_id(self, candidate_id: str) -> Optional[dict]:
       try:
           profile = self.__profileRepo.get_by_candidate_id(candidate_id)
           if not profile:
               return None

           profile_dto = CandidateProfileDTO().dump(profile)
           matches = self.__matchRepo.get_by_profile_id(profile.id)
           matches_data = []

           for match in matches:
               match_dto = CandidateProfileMatchDTO().dump(match)

               # Get Technical Skills
               tech_skills = self.__technicalSkillsRepo.get_by_match_id(match.id)
               if tech_skills:
                   tech_dto = CandidateProfileTechnicalSkillsDTO().dump(tech_skills)
                   tech_dto['skillMatches'] = CandidateProfileTechnicalSkillMatchDTO(many=True).dump(
                       self.__technicalSkillMatchRepo.get_by_technical_skills_id(tech_skills.id)
                   )
                   tech_dto['frameworksAndTools'] = CandidateProfileFrameworkToolDTO(many=True).dump(
                       self.__frameworkToolRepo.get_by_technical_skills_id(tech_skills.id)
                   )
                   match_dto['technicalSkills'] = tech_dto

               # Get Soft Skills
               soft_skills = self.__softSkillsRepo.get_by_match_id(match.id)
               if soft_skills:
                   soft_dto = CandidateProfileSoftSkillsDTO().dump(soft_skills)
                   soft_dto['skillMatches'] = CandidateProfileSoftSkillMatchDTO(many=True).dump(
                       self.__softSkillMatchRepo.get_by_soft_skills_id(soft_skills.id)
                   )
                   match_dto['softSkills'] = soft_dto

               # Get Experience
               experience = self.__experienceRepo.get_by_match_id(match.id)
               if experience:
                   exp_dto = CandidateProfileExperienceDTO().dump(experience)
                   exp_dto['industryExperience'] = CandidateProfileIndustryExperienceDTO(many=True).dump(
                       self.__industryExpRepo.get_by_experience_id(experience.id)
                   )
                   exp_dto['relevantRoles'] = CandidateProfileRelevantRoleDTO(many=True).dump(
                       self.__relevantRoleRepo.get_by_experience_id(experience.id)
                   )
                   match_dto['experience'] = exp_dto

               # Get Education
               education = self.__educationRepo.get_by_match_id(match.id)
               if education:
                   edu_dto = CandidateProfileEducationDTO().dump(education)
                   edu_dto['degrees'] = CandidateProfileDegreeDTO(many=True).dump(
                       self.__degreeRepo.get_by_education_id(education.id)
                   )
                   match_dto['education'] = edu_dto

               # Get Projects
               projects = self.__projectsRepo.get_by_match_id(match.id)
               if projects:
                   proj_dto = CandidateProfileProjectsDTO().dump(projects)
                   proj_dto['items'] = CandidateProfileProjectDTO(many=True).dump(
                       self.__projectRepo.get_by_projects_id(projects.id)
                   )
                   match_dto['projects'] = proj_dto

               # Get Social Presence
               social = self.__socialPresenceRepo.get_by_match_id(match.id)
               if social:
                   match_dto['socialPresence'] = CandidateProfileSocialPresenceDTO().dump(social)

               matches_data.append(match_dto)

           profile_dto['matches'] = matches_data
           return profile_dto

       except Exception as e:
           raise CustomError(str(e), 400)

   def update_profile(self, profile_id: str, updated_data: dict) -> Optional[dict]:
       try:
           profile = self.__profileRepo.get_by_id(profile_id)
           if not profile:
               return None

           for key, value in updated_data.items():
               if hasattr(profile, key):
                   setattr(profile, key, value)

           self.__profileRepo.update(profile)
           return self.get_profile_by_candidate_id(profile.candidate_id)

       except Exception as e:
           raise CustomError(str(e), 400)

   def delete_profile(self, profile_id: str) -> bool:
       try:
           profile = self.__profileRepo.get_by_id(profile_id)
           if not profile:
               return False

           matches = self.__matchRepo.get_by_profile_id(profile_id)
           for match in matches:
               self._delete_match_related_data(match)
               self.__matchRepo.delete(match)

           self.__profileRepo.delete(profile)
           return True

       except Exception as e:
           raise CustomError(str(e), 400)

   def _delete_match_related_data(self, match):
       # Delete Technical Skills and related data
       tech_skills = self.__technicalSkillsRepo.get_by_match_id(match.id)
       if tech_skills:
           for skill_match in self.__technicalSkillMatchRepo.get_by_technical_skills_id(tech_skills.id):
               self.__technicalSkillMatchRepo.delete(skill_match)
           for tool in self.__frameworkToolRepo.get_by_technical_skills_id(tech_skills.id):
               self.__frameworkToolRepo.delete(tool)
           self.__technicalSkillsRepo.delete(tech_skills)

       # Delete Soft Skills and related data
       soft_skills = self.__softSkillsRepo.get_by_match_id(match.id)
       if soft_skills:
           for skill_match in self.__softSkillMatchRepo.get_by_soft_skills_id(soft_skills.id):
               self.__softSkillMatchRepo.delete(skill_match)
           self.__softSkillsRepo.delete(soft_skills)

       # Delete Experience and related data
       experience = self.__experienceRepo.get_by_match_id(match.id)
       if experience:
           for ind_exp in self.__industryExpRepo.get_by_experience_id(experience.id):
               self.__industryExpRepo.delete(ind_exp)
           for role in self.__relevantRoleRepo.get_by_experience_id(experience.id):
               self.__relevantRoleRepo.delete(role)
           self.__experienceRepo.delete(experience)

       # Delete Education and related data
       education = self.__educationRepo.get_by_match_id(match.id)
       if education:
           for degree in self.__degreeRepo.get_by_education_id(education.id):
               self.__degreeRepo.delete(degree)
           self.__educationRepo.delete(education)

       # Delete Projects and related data
       projects = self.__projectsRepo.get_by_match_id(match.id)
       if projects:
           for project in self.__projectRepo.get_by_projects_id(projects.id):
               self.__projectRepo.delete(project)
           self.__projectsRepo.delete(projects)

       # Delete Social Presence
       social = self.__socialPresenceRepo.get_by_match_id(match.id)
       if social:
           self.__socialPresenceRepo.delete(social)

   def get_all_profiles(self) -> List[dict]:
       try:
           profiles = self.__profileRepo.get_all()
           return [self.get_profile_by_candidate_id(profile.candidate_id)
                  for profile in profiles if profile]
       except Exception as e:
           raise CustomError(str(e), 400)