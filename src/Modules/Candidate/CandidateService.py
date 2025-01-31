from datetime import datetime
import uuid

from src.Helpers.ErrorHandling import CustomError
from src.Modules.Candidate.CandidateDTOs import CandidateDTO
from src.Modules.Candidate.CandidateModels import Candidate, CandidateStatus, CandidatePipelineStatus
from src.Modules.Candidate.CandidateRepository import CandidateRepository
from src.Modules.Interviews.InterviewDTOs import InterviewDTO
from src.Modules.Interviews.InterviewServices import InterviewService


class CandidateService:
    def __init__(self):
        self.__candidate_repository = CandidateRepository()
        self.__interview_service = InterviewService()

    def fetch_all(self, filters=None):
        try:
            candidates = self.__candidate_repository.get_all_candidates(filters)
            if len(candidates) == 0:
                raise Exception("No candidates found")
            return CandidateDTO(many=True).dump(candidates)
        except Exception as e:
            raise CustomError(str(e), 400)

    def fetch_by_id(self, candidate_id):
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)
            if not candidate:
                raise CustomError("Candidate not found", 404)
            return CandidateDTO(many=False).dump(candidate)
        except Exception as e:
            raise CustomError(str(e), 400)

    def create_candidate(self, candidate_data):
        try:
            # Check if candidate with email already exists
            existing_candidate = self.__candidate_repository.get_candidate_by_email(candidate_data['email'])
            if existing_candidate:
                raise CustomError("Candidate with this email already exists", 400)

            candidate = Candidate(
                id=str(uuid.uuid4()),
                job_id=candidate_data['job_id'],
                first_name=candidate_data['first_name'],
                last_name=candidate_data['last_name'],
                email=candidate_data['email'],
                phone=candidate_data.get('phone'),
                resume_url=candidate_data.get('resume_url'),
                current_company=candidate_data.get('current_company'),
                current_position=candidate_data.get('current_position'),
                years_of_experience=candidate_data.get('years_of_experience')
            )

            saved_candidate = self.__candidate_repository.save_candidate(candidate)
            return CandidateDTO(many=False).dump(saved_candidate)
        except Exception as e:
            raise CustomError(str(e), 400)

    def update_candidate(self, candidate_id, candidate_data):
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)
            if not candidate:
                raise CustomError("Candidate not found", 404)

            updatable_fields = {
                'first_name', 'last_name', 'phone', 'current_company',
                'current_position', 'years_of_experience', 'status'
            }

            for field in candidate_data:
                if field in updatable_fields:
                    setattr(candidate, field, candidate_data[field])

            candidate.updated_at = datetime.utcnow()

            self.__candidate_repository.update_candidate(candidate)
            return CandidateDTO(many=False).dump(candidate)
        except Exception as e:
            raise CustomError(str(e), 400)

    def schedule_interview(self, candidate_id, interview_data):
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)
            if not candidate:
                raise CustomError("Candidate not found", 404)

            # Update candidate status
            candidate.status = CandidateStatus.INTERVIEWING
            self.__candidate_repository.update_candidate(candidate)

            # Create interview
            interview_data['candidate_id'] = candidate_id
            interview_data['job_id'] = candidate.job_id

            return self.__interview_service.schedule_interview(interview_data)
        except Exception as e:
            raise CustomError(str(e), 400)

    def get_candidate_interviews(self, candidate_id):
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)
            if not candidate:
                raise CustomError("Candidate not found", 404)

            # Interviews are loaded through the relationship
            return InterviewDTO(many=True).dump(candidate.interviews)
        except Exception as e:
            raise CustomError(str(e), 400)

    def update_candidate_status(self, candidate_id, new_status):
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)
            if not candidate:
                raise CustomError("Candidate not found", 404)

            candidate.status = new_status
            candidate.updated_at = datetime.utcnow()

            self.__candidate_repository.update_candidate(candidate)
            return CandidateDTO(many=False).dump(candidate)
        except Exception as e:
            raise CustomError(str(e), 400)

    def search_candidates(self, search_term):
        try:
            candidates = self.__candidate_repository.search_candidates(search_term)
            return CandidateDTO(many=True).dump(candidates)
        except Exception as e:
            raise CustomError(str(e), 400)

    def update_pipeline_status(self, candidate_id: str, status: CandidatePipelineStatus) -> dict:
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)

            if not candidate:
                raise CustomError("Candidate not found", 404)

            candidate.pipeline_status = status
            candidate.updated_at = datetime.utcnow()

            self.__candidate_repository.update_candidate(candidate)
            return CandidateDTO(many=False).dump(candidate)

        except Exception as e:
            raise CustomError(str(e), 400)

    def get_pipeline_status(self, candidate_id):
        try:
            candidate = self.__candidate_repository.get_candidate_by_id(candidate_id)
            if not candidate:
                raise CustomError("Candidate not found", 404)
            return CandidatePipelineStatus(candidate.pipeline_status)
        except Exception as e:
            raise CustomError(str(e), 400)

    # Success state convenience methods
    def set_pipeline_status_to_text_extraction(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.EXTRACT_TEXT)

    def set_pipeline_status_to_google_scrape(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.GOOGLE_SCRAPE)

    def set_pipeline_status_to_linkedin_scrape(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.LINKEDIN_SCRAPE)

    def set_pipeline_status_to_github_scrape(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.GITHUB_SCRAPE)

    def set_pipeline_status_to_profile_creation(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.PROFILE_CREATION)

    def set_pipeline_status_to_profile_created(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.PROFILE_CREATED)

    # Failed state convenience methods
    def set_pipeline_status_to_text_extraction_failed(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.EXTRACT_TEXT_FAILED)

    def set_pipeline_status_to_google_scrape_failed(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.GOOGLE_SCRAPE_FAILED)

    def set_pipeline_status_to_linkedin_scrape_failed(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.LINKEDIN_SCRAPE_FAILED)

    def set_pipeline_status_to_github_scrape_failed(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.GITHUB_SCRAPE_FAILED)

    def set_pipeline_status_to_profile_creation_failed(self, candidate_id: str) -> dict:
        return self.update_pipeline_status(candidate_id, CandidatePipelineStatus.PROFILE_CREATION_FAILED)
