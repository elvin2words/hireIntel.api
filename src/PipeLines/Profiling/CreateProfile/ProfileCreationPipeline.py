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

# from flask import Flask
#
# from src.Modules.Candidate.CandidateService import CandidateService
# from src.Modules.PipeLineData.ProfileCreationData.ProfileCreationService import CandidateProfileDataService
# from src.PipeLines.PipeLineManagement.PipeLineBase import PipelineConfig, BasePipeline
# from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
# from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor
# from src.PipeLines.Profiling.CreateProfile.ProfileCreation import ProfileCreationService
# from src.Modules.Candidate.CandidateModels import Candidate, CandidatePipelineStatus
# from src.Helpers.ErrorHandling import CustomError
#
#
# class ProfileCreationConfig(PipelineConfig):
#     def __init__(self,
#                  name: str = "profile_creation",
#                  batch_size: int = 10,
#                  process_interval: int = 300,  # 5 minutes
#                  technical_weight: float = 0.4,
#                  experience_weight: float = 0.35,
#                  github_weight: float = 0.25,
#                  min_passing_score: float = 70.0):
#         super().__init__(name, batch_size, process_interval=process_interval)
#         self.technical_weight = technical_weight
#         self.experience_weight = experience_weight
#         self.github_weight = github_weight
#         self.min_passing_score = min_passing_score
#
#
# class ProfileCreationPipeline(BasePipeline):
#     def __init__(self, app: Flask, config: ProfileCreationConfig, monitor: PipelineMonitor):
#         super().__init__(app, config, monitor)
#         self.config: ProfileCreationConfig = config
#         self.__profileCreation = ProfileCreationService()
#         self.__candidateService = CandidateService()
#         self.__profileCreationDataService = CandidateProfileDataService()
#
#     def process_batch(self):
#         """Process a batch of candidates for profile creation"""
#         try:
#             # Get candidates ready for profile creation (INPUT)
#             candidates = Candidate.query.filter_by(
#                 pipeline_status=CandidatePipelineStatus.PROFILE_CREATION
#             ).limit(self.config.batch_size).all()
#
#             if not candidates:
#                 self.logger.info("No candidates found for profile creation")
#                 return
#
#             self.logger.info(f"Processing {len(candidates)} candidates for profile creation")
#
#             for candidate in candidates:
#                 try:
#                     self._process_candidate(candidate)
#                 except Exception as e:
#                     self.logger.error(f"Failed to create profile for candidate {candidate.id}: {str(e)}")
#                     self.__candidateService.set_pipeline_status_to_profile_creation_failed(candidate.id)
#
#         except Exception as e:
#             self.logger.error(f"Batch processing failed: {str(e)}")
#             raise CustomError(f"Profile creation pipeline failed: {str(e)}", 400)
#
#
#     def _process_candidate(self, candidate : Candidate) -> None:
#
#         try:
#             self.logger.info(f"Starting Profile creation for candidate ID: {candidate.id}")
#
#             self.monitor.update_state(
#                 self.config.name,
#                 PipelineStatus.RUNNING,
#                 message=f"Creating profile for candidate {candidate.id}"
#             )
#
#             # profile creation
#             profile = self.__profileCreation.create_profile(candidate.id, candidate.job_id)
#
#             if not profile:
#                 self.logger.info(f"No profile found for candidate {candidate.id}")
#                 self.__candidateService.set_pipeline_status_to_profile_creation_failed(candidate.id)
#                 return
#
#             # Save the created profile (OUT PUT)
#             self.__profileCreationDataService.save_profile(candidate.id,candidate.job_id, profile)
#             self.__candidateService.set_pipeline_status_to_profile_created(candidate.id)
#
#             self.logger.info(f"Successfully save profile data for candidate: {candidate.id}")
#
#         except Exception as e:
#             self.monitor.update_state(
#                 self.config.name,
#                 PipelineStatus.ERROR,
#                 error_message=f"Failed to create profile for candidate {candidate.id}: {str(e)}"
#             )
#             self.logger.error(f"Pipeline error for candidate {candidate.id}: {str(e)}")
#             self.__candidateService.set_pipeline_status_to_profile_creation_failed(candidate.id)
#             raise CustomError(f"Error processing candidate: {str(e)}", 400)
#
