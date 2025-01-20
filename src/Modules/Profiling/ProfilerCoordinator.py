from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.Helpers.PipelineMonitor import PipelineMonitor, PipelineStatus
from src.Modules.Profiling.PipeLines.CreateProfile.ProfileCreationPipeline import MonitoredProfileCreationPipeline
from src.Modules.Profiling.PipeLines.DataScraping.GoogleScrapingPipeline import GoogleScrapingPipeline
from src.Modules.Profiling.PipeLines.TextExtraction.TextExtractionPipeline import  MonitoredTextExtractionPipeline
from src.Modules.Profiling.PipeLines.DataScraping.GitHubScrapingPipeline import GitHubScrapingPipeline
from src.Helpers.ErrorHandling import CustomError

class MonitoredProfilerCoordinator:
    def __init__(self, github_token: str, google_api_key: str, monitor: PipelineMonitor):
        self.scheduler = BackgroundScheduler()
        self.monitor = monitor

        # Initialize pipelines with monitor
        self.text_extraction_pipeline = MonitoredTextExtractionPipeline(monitor)
        self.github_pipeline = GitHubScrapingPipeline(github_token)  # Add monitoring if needed
        self.google_pipeline = GoogleScrapingPipeline(google_api_key)  # Add monitoring if needed
        self.profile_pipeline = MonitoredProfileCreationPipeline(monitor)

        # Pipeline execution intervals (in minutes)
        self.intervals = {
            'text_extraction': 5,
            'github_scraping': 10,
            'google_scraping': 10,
            'profile_creation': 15
        }

    def _monitored_text_extraction(self):
        """Wrapper for text extraction pipeline with monitoring"""
        try:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.RUNNING,
                "Triggering text extraction pipeline"
            )
            self.text_extraction_pipeline.run_pipeline()

        except Exception as e:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.ERROR,
                error_message=f"Text extraction schedule failed: {str(e)}"
            )

    def _monitored_profile_creation(self):
        """Wrapper for profile creation pipeline with monitoring"""
        try:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.RUNNING,
                "Triggering profile creation pipeline"
            )
            self.profile_pipeline.run_pipeline()

        except Exception as e:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.ERROR,
                error_message=f"Profile creation schedule failed: {str(e)}"
            )

    def start_scheduling(self):
        """Initialize and start all pipeline schedules with monitoring"""
        try:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.RUNNING,
                "Initializing pipeline schedules"
            )

            # Schedule text extraction pipeline
            self.scheduler.add_job(
                func=self._monitored_text_extraction,
                trigger=IntervalTrigger(minutes=self.intervals['text_extraction']),
                id='text_extraction',
                name='Resume Text Extraction Pipeline'
            )

            # Schedule GitHub scraping pipeline
            self.scheduler.add_job(
                func=self.github_pipeline.run_pipeline,
                trigger=IntervalTrigger(minutes=self.intervals['github_scraping']),
                id='github_scraping',
                name='GitHub Data Scraping Pipeline'
            )

            # Schedule Google scraping pipeline
            self.scheduler.add_job(
                func=self.google_pipeline.run_pipeline,
                trigger=IntervalTrigger(minutes=self.intervals['google_scraping']),
                id='google_scraping',
                name='Google Search Scraping Pipeline'
            )

            # Schedule profile creation pipeline
            self.scheduler.add_job(
                func=self._monitored_profile_creation,
                trigger=IntervalTrigger(minutes=self.intervals['profile_creation']),
                id='profile_creation',
                name='Profile Creation Pipeline'
            )

            # Start the scheduler
            self.scheduler.start()

            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.RUNNING,
                "All pipeline schedules started successfully",
                details={
                    'active_pipelines': list(self.intervals.keys()),
                    'intervals': self.intervals
                }
            )

        except Exception as e:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.ERROR,
                error_message=f"Failed to start pipeline scheduling: {str(e)}"
            )
            raise CustomError(f"Failed to start pipeline scheduling: {str(e)}", 500)

    def stop_scheduling(self):
        """Stop all scheduled pipelines"""
        try:
            self.scheduler.shutdown()
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.IDLE,
                "All pipeline schedules stopped"
            )
        except Exception as e:
            self.monitor.update_pipeline_state(
                "scheduler",
                PipelineStatus.ERROR,
                error_message=f"Failed to stop pipeline scheduling: {str(e)}"
            )

    def process_new_candidate(self, candidate_id: str):
        """Manually trigger processing for a new candidate"""
        try:
            self.monitor.update_pipeline_state(
                "manual_processing",
                PipelineStatus.RUNNING,
                f"Starting manual processing for candidate {candidate_id}"
            )

            self.text_extraction_pipeline.process_candidate(candidate_id)

            self.monitor.update_pipeline_state(
                "manual_processing",
                PipelineStatus.IDLE,
                f"Successfully initiated processing for candidate {candidate_id}"
            )

        except Exception as e:
            self.monitor.update_pipeline_state(
                "manual_processing",
                PipelineStatus.ERROR,
                error_message=f"Failed to start candidate processing: {str(e)}"
            )
            raise CustomError(f"Failed to start candidate processing: {str(e)}", 400)