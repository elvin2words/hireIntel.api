from flask import Flask
from typing import List, Optional, Dict

from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationService import CandidateProfileDataService
from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
from src.PipeLines.Profiling.CreateProfile.ProfileCreation import ProfileCreationService
from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
from src.Helpers.ErrorHandling import CustomError


class ProfileCreationConfig(PipelineConfig):
    def __init__(self,
                 name: str = "profile_creation",
                 batch_size: int = 10,
                 process_interval: int = 300,
                 technical_weight: float = 0.4,
                 experience_weight: float = 0.35,
                 github_weight: float = 0.25,
                 min_passing_score: float = 70.0):
        super().__init__(name, batch_size, process_interval=process_interval)
        self.technical_weight = technical_weight
        self.experience_weight = experience_weight
        self.github_weight = github_weight
        self.min_passing_score = min_passing_score


class ProfileCreationPipeline(BasePipeline):
    def __init__(self, app: Flask, config: ProfileCreationConfig, monitor: PipelineMonitor):
        super().__init__(app, config, monitor)
        self.config: ProfileCreationConfig = config
        self.__profileCreation = ProfileCreationService()
        self.__candidateService = CandidateService()
        self.__profileCreationDataService = CandidateProfileDataService()

    def get_input_data(self) -> List[Candidate]:
        return (Candidate.query
                .filter_by(pipeline_status=CandidatePipelineStatus.PROFILE_CREATION)
                .limit(self.config.batch_size)
                .all())

    def process_item(self, candidate: Candidate) -> Optional[Dict]:
        self.logger.info(f"Creating profile for candidate ID: {candidate.id}")
        profile = self.__profileCreation.create_profile(candidate.id, candidate.job_id)

        if not profile:
            raise CustomError(f"No profile generated for candidate {candidate.id}", 400)

        return {
            'candidate_id': candidate.id,
            'job_id': candidate.job_id,
            'profile': profile
        }

    def update_output(self, results: List[Dict]) -> None:
        for result in results:
            if result:
                self.__profileCreationDataService.save_profile(
                    result['candidate_id'],
                    result['job_id'],
                    result['profile']
                )
                self.__candidateService.set_pipeline_status_to_profile_created(result['candidate_id'])

    def handle_item_failure(self, candidate: Candidate, error: Exception) -> None:
        self.logger.error(f"Failed to create profile for candidate {candidate.id}: {str(error)}")
        self.__candidateService.set_pipeline_status_to_profile_creation_failed(candidate.id)