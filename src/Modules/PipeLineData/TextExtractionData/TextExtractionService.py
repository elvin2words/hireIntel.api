from datetime import datetime
import uuid
from typing import Dict, List, Optional

from src.Helpers.ErrorHandling import CustomError
from src.Modules.PipeLineData.TextExtractionData.TextExtractionDTOs import (
    ResumeDTO, EducationDTO, WorkExperienceDTO, TechnicalSkillDTO, SoftSkillDTO, KeywordDTO
)
from src.Modules.PipeLineData.TextExtractionData.TextExtractionModels import (
    Resume, Education, WorkExperience, TechnicalSkill, SoftSkill, Keyword
)
from src.Modules.PipeLineData.TextExtractionData.TextExtractionRepository import (
    ResumeRepository, EducationRepository, WorkExperienceRepository,
    TechnicalSkillRepository, SoftSkillRepository, KeywordRepository
)

class TextExtractionDataService:
    def __init__(self):
        self.__resume_repository = ResumeRepository()
        self.__education_repository = EducationRepository()
        self.__experience_repository = WorkExperienceRepository()
        self.__technical_skill_repository = TechnicalSkillRepository()
        self.__soft_skill_repository = SoftSkillRepository()
        self.__keyword_repository = KeywordRepository()

        # Initialize DTOs
        self.__resume_dto = ResumeDTO()
        self.__education_dto = EducationDTO()
        self.__work_experience_dto = WorkExperienceDTO()
        self.__technical_skill_dto = TechnicalSkillDTO()
        self.__soft_skill_dto = SoftSkillDTO()
        self.__keyword_dto = KeywordDTO()

    def get_all_resumes(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get all resumes with optional filtering
        Returns a list of resume DTOs
        """
        try:
            resumes = self.__resume_repository.get_all_with_filters(filters)
            if not resumes:
                raise CustomError("No resumes found", 404)
            return self.__resume_dto.dump(resumes, many=True)
        except Exception as e:
            raise CustomError(str(e), 400)

    def get_resume_by_id(self, resume_id: str) -> Dict:
        """
        Get a single resume by ID
        Returns a resume DTO
        """
        try:
            resume = self.__resume_repository.get_by_id(resume_id)
            if not resume:
                raise CustomError("Resume not found", 404)
            return self.__resume_dto.dump(resume)
        except Exception as e:
            raise CustomError(str(e), 400)

    def get_resume_by_candidate_id(self, candidate_id: str) -> Dict:
        """
        Get a single candidate by ID
        Returns a resume DTO
        """
        try:
            print("Inside resume get Service")
            resumes = self.__resume_repository.get_by_candidate_id(candidate_id)
            print("this is my resume: ", resumes)

            if not resumes or len(resumes) == 0:
                raise CustomError("Resume not found", 404)

            # Take the first resume since we expect one resume per candidate
            resume = resumes[0]

            # Transform the data to match DTO structure
            resume_data = {
                'personal_information': {
                    'full_name': resume.full_name,
                    'email': resume.email,
                    'phone_numbers': resume.phone_numbers,
                    'address': resume.address,
                    'linkedin_url': resume.linkedin_url,
                    'github_url': resume.github_url,
                    'github_handle': resume.github_handle,
                    'linkedin_handle': resume.linkedin_handle,
                    'portfolio_url': resume.portfolio_url
                },
                'education': [
                    {
                        'institution': edu.institution,
                        'degree': edu.degree,
                        'field_of_study': edu.field_of_study,
                        'start_date': edu.start_date,
                        'end_date': edu.end_date,
                        'gpa': edu.gpa,
                        'description': edu.description,
                        'location': edu.location
                    } for edu in resume.education
                ],
                'work_experience': [
                    {
                        'company': exp.company,
                        'position': exp.position,
                        'employment_type': exp.employment_type,
                        'start_date': exp.start_date,
                        'end_date': exp.end_date,
                        'is_current': exp.is_current,
                        'location': exp.location,
                        'description': exp.description,
                        'achievements': exp.achievements
                    } for exp in resume.work_experience
                ],
                'technical_skills': [
                    {
                        'skill_name': skill.skill_name,
                        'proficiency_level': skill.proficiency_level,
                        'years_experience': skill.years_experience
                    } for skill in resume.technical_skills
                ],
                'soft_skills': [
                    {
                        'skill_name': skill.skill_name
                    } for skill in resume.soft_skills
                ],
                'keywords': [
                    {
                        'keyword': kw.keyword,
                        'category': kw.category
                    } for kw in resume.keywords
                ]
            }

            return self.__resume_dto.dump(resume_data)
        except Exception as e:
            raise CustomError(str(e), 400)

    def create_resume(self, resume_data: Dict, candidate_id: str) -> Dict:
        """
        Create a new resume with all related entities
        """
        try:
            # Validate input data using DTO
            errors = self.__resume_dto.validate(resume_data)
            if errors:
                raise CustomError(f"Invalid resume data: {errors}", 400)

            personal_info = resume_data['personalInformation']

            # Create main resume record
            resume = Resume(
                id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                full_name=personal_info['fullName'],
                email=personal_info['email'],
                phone_numbers=personal_info.get('phoneNumbers'),
                address=personal_info.get('address'),
                linkedin_url=personal_info.get('linkedinUrl'),
                github_url=personal_info.get('githubUrl'),
                linkedin_handle=personal_info.get('linkedinHandle'),
                github_handle=personal_info.get('githubHandle'),
                portfolio_url=personal_info.get('portfolioUrl')
            )

            # Save the resume
            self.__resume_repository.create(resume)

            # Create education records
            if 'education' in resume_data:
                for edu_data in resume_data['education']:
                    education = Education(
                        id=str(uuid.uuid4()),
                        resume_id=resume.id,
                        institution=edu_data['institution'],
                        degree=edu_data['degree'],
                        field_of_study=edu_data.get('fieldOfStudy'),
                        start_date=edu_data.get('startDate'),
                        end_date=edu_data.get('endDate'),
                        gpa=edu_data.get('gpa'),
                        description=edu_data.get('description'),
                        location=edu_data.get('location')
                    )
                    self.__education_repository.create(education)

            # Create work experiences
            if 'workExperience' in resume_data:
                for exp_data in resume_data['workExperience']:
                    experience = WorkExperience(
                        id=str(uuid.uuid4()),
                        resume_id=resume.id,
                        company=exp_data['company'],
                        position=exp_data['position'],
                        employment_type=exp_data.get('employmentType'),
                        start_date=exp_data.get('startDate'),
                        end_date=exp_data.get('endDate'),
                        is_current=exp_data.get('isCurrent', False),
                        location=exp_data.get('location'),
                        description=exp_data.get('description'),
                        achievements=exp_data.get('achievements')
                    )
                    self.__experience_repository.create(experience)

            # Create technical skills
            if 'technicalSkills' in resume_data:
                for skill_data in resume_data['technicalSkills']:
                    skill = TechnicalSkill(
                        id=str(uuid.uuid4()),
                        resume_id=resume.id,
                        skill_name=skill_data['skillName'],
                        proficiency_level=skill_data.get('proficiencyLevel'),
                        years_experience=skill_data.get('yearsExperience')
                    )
                    self.__technical_skill_repository.create(skill)

            # Create soft skills
            if 'softSkills' in resume_data:
                for skill_data in resume_data['softSkills']:
                    skill = SoftSkill(
                        id=str(uuid.uuid4()),
                        resume_id=resume.id,
                        skill_name=skill_data['skillName']
                    )
                    self.__soft_skill_repository.create(skill)

            # Create keywords
            if 'keywords' in resume_data:
                for keyword_data in resume_data['keywords']:
                    keyword = Keyword(
                        id=str(uuid.uuid4()),
                        resume_id=resume.id,
                        keyword=keyword_data['keyword'],
                        category=keyword_data.get('category')
                    )
                    self.__keyword_repository.create(keyword)

            return self.get_resume_by_id(resume.id)

        except Exception as e:
            raise CustomError(str(e), 400)

    def update_resume(self, resume_id: str, resume_data: Dict) -> Dict:
        """
        Update an existing resume and its related entities
        Returns updated resume DTO
        """
        try:
            resume = self.__resume_repository.get_by_id(resume_id)
            if not resume:
                raise CustomError("Resume not found", 404)

            # Validate update data using DTO
            errors = self.__resume_dto.validate(resume_data, partial=True)
            if errors:
                raise CustomError(f"Invalid resume data: {errors}", 400)

            # If email is being updated, check for duplicates
            if 'email' in resume_data and resume_data['email'] != resume.email:
                if self.__resume_repository.get_by_email(resume_data['email']):
                    raise CustomError("Resume with this email already exists", 400)

            # Update main resume fields
            self.__update_resume_fields(resume, resume_data)

            # Update related entities if provided in the update data
            if 'education' in resume_data:
                self.__update_education_records(resume.id, resume_data['education'])

            if 'experiences' in resume_data:
                self.__update_experience_records(resume.id, resume_data['experiences'])

            if 'technicalSkills' in resume_data:
                self.__update_technical_skill_records(resume.id, resume_data['technicalSkills'])

            if 'softSkills' in resume_data:
                self.__update_soft_skill_records(resume.id, resume_data['softSkills'])

            if 'keywords' in resume_data:
                self.__update_keyword_records(resume.id, resume_data['keywords'])

            # Update the resume
            self.__resume_repository.update(resume)
            return self.get_resume_by_id(resume.id)
        except Exception as e:
            raise CustomError(str(e), 400)

    def delete_resume(self, resume_id: str) -> None:
        """
        Delete a resume and all its related entities
        """
        try:
            resume = self.__resume_repository.get_by_id(resume_id)
            if not resume:
                raise CustomError("Resume not found", 404)

            self.__resume_repository.delete(resume)
        except Exception as e:
            raise CustomError(str(e), 400)

    def __update_resume_fields(self, resume: Resume, data: Dict) -> None:
        """
        Update the main resume fields
        """
        resume.email = data.get('email', resume.email)
        resume.full_name = data.get('full_name', resume.full_name)
        resume.phone_numbers = data.get('phone_numbers', resume.phone_numbers)
        resume.address = data.get('address', resume.address)
        resume.linkedin_url = data.get('linkedin_url', resume.linkedin_url)
        resume.github_url = data.get('github_url', resume.github_url)
        resume.portfolio_url = data.get('portfolio_url', resume.portfolio_url)
        resume.updated_at = datetime.utcnow()

    def __create_education_records(self, resume_id: str, education_data: List[Dict]) -> None:
        """
        Create education records for a resume
        """
        for edu_data in education_data:
            # Validate education data
            errors = self.__education_dto.validate(edu_data)
            if errors:
                raise CustomError(f"Invalid education data: {errors}", 400)

            education = Education(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                institution=edu_data['institution'],
                degree=edu_data['degree'],
                field_of_study=edu_data['field_of_study'],
                start_date=edu_data['start_date'],
                end_date=edu_data.get('end_date'),
                gpa=edu_data.get('gpa'),
                description=edu_data.get('description'),
                location=edu_data.get('location')
            )
            self.__education_repository.create(education)

    def __create_experience_records(self, resume_id: str, experience_data: List[Dict]) -> None:
        """
        Create work experience records for a resume
        """
        for exp_data in experience_data:
            # Validate experience data
            errors = self.__work_experience_dto.validate(exp_data)
            if errors:
                raise CustomError(f"Invalid work experience data: {errors}", 400)

            experience = WorkExperience(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                company=exp_data['company'],
                position=exp_data['position'],
                employment_type=exp_data.get('employment_type'),
                start_date=exp_data['start_date'],
                end_date=exp_data.get('end_date'),
                is_current=exp_data.get('is_current', False),
                location=exp_data.get('location'),
                description=exp_data.get('description'),
                achievements=exp_data.get('achievements')
            )
            self.__experience_repository.create(experience)

    def __create_technical_skill_records(self, resume_id: str, skill_data: List[Dict]) -> None:
        """
        Create technical skill records for a resume
        """
        for skill in skill_data:
            # Validate technical skill data
            errors = self.__technical_skill_dto.validate(skill)
            if errors:
                raise CustomError(f"Invalid technical skill data: {errors}", 400)

            technical_skill = TechnicalSkill(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                skill_name=skill['skill_name'],
                proficiency_level=skill.get('proficiency_level'),
                years_experience=skill.get('years_experience')
            )
            self.__technical_skill_repository.create(technical_skill)

    def __create_soft_skill_records(self, resume_id: str, skill_data: List[Dict]) -> None:
        """
        Create soft skill records for a resume
        """
        for skill in skill_data:
            # Validate soft skill data
            errors = self.__soft_skill_dto.validate(skill)
            if errors:
                raise CustomError(f"Invalid soft skill data: {errors}", 400)

            soft_skill = SoftSkill(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                skill_name=skill['skill_name']
            )
            self.__soft_skill_repository.create(soft_skill)

    def __create_keyword_records(self, resume_id: str, keyword_data: List[Dict]) -> None:
        """
        Create keyword records for a resume
        """
        for kw in keyword_data:
            # Validate keyword data
            errors = self.__keyword_dto.validate(kw)
            if errors:
                raise CustomError(f"Invalid keyword data: {errors}", 400)

            keyword = Keyword(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                keyword=kw['keyword'],
                category=kw.get('category')
            )
            self.__keyword_repository.create(keyword)

    def __update_education_records(self, resume_id: str, education_data: List[Dict]) -> None:
        """
        Update education records for a resume
        """
        current_records = self.__education_repository.get_by_resume_id(resume_id)
        for record in current_records:
            self.__education_repository.delete(record)
        self.__create_education_records(resume_id, education_data)

    def __update_experience_records(self, resume_id: str, experience_data: List[Dict]) -> None:
        """
        Update work experience records for a resume
        """
        current_records = self.__experience_repository.get_by_resume_id(resume_id)
        for record in current_records:
            self.__experience_repository.delete(record)
        self.__create_experience_records(resume_id, experience_data)

    def __update_technical_skill_records(self, resume_id: str, skill_data: List[Dict]) -> None:
        """
        Update technical skill records for a resume
        """
        current_records = self.__technical_skill_repository.get_by_resume_id(resume_id)
        for record in current_records:
            self.__technical_skill_repository.delete(record)
        self.__create_technical_skill_records(resume_id, skill_data)

    def __update_soft_skill_records(self, resume_id: str, skill_data: List[Dict]) -> None:
        """
        Update soft skill records for a resume
        """
        current_records = self.__soft_skill_repository.get_by_resume_id(resume_id)
        for record in current_records:
            self.__soft_skill_repository.delete(record)
        self.__create_soft_skill_records(resume_id, skill_data)

    def __update_keyword_records(self, resume_id: str, keyword_data: List[Dict]) -> None:
        """
        Update keyword records for a resume
        """
        current_records = self.__keyword_repository.get_by_resume_id(resume_id)
        for record in current_records:
            self.__keyword_repository.delete(record)
        self.__create_keyword_records(resume_id, keyword_data)