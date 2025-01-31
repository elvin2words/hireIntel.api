from abc import ABC, abstractmethod
from typing import Optional
import threading
import logging
from flask import Flask

from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus


class PipelineConfig:
    def __init__(self,
                 name: str,
                 batch_size: int = 10,
                 idle_time: int = 60,  # seconds
                 process_interval: int = 300,  # seconds
                 **kwargs):
        self.name = name
        self.batch_size = batch_size
        self.idle_time = idle_time
        self.process_interval = process_interval
        self.additional_config = kwargs


class BasePipeline(ABC):
    def __init__(self, app: Flask, config: PipelineConfig,
                 monitor: 'PipelineMonitor'):
        self.app = app
        self.config = config
        self.monitor = monitor
        self.thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        # self.pipeline_tracking_service = pipeline_tracking_service

        # Configure logging
        self.logger = logging.getLogger(f"pipeline.{config.name}")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    @abstractmethod
    def process_batch(self) -> None:
        """Process a single batch of items"""
        pass

    def _run_pipeline(self):
        """Internal method to run the pipeline loop"""
        with self.app.app_context():
            while not self.stop_flag.is_set():
                try:
                    self.monitor.update_state(
                        self.config.name,
                        PipelineStatus.RUNNING,
                        "Starting batch processing"
                    )

                    self.process_batch()

                    self.monitor.update_state(
                        self.config.name,
                        PipelineStatus.IDLE,
                        "Batch processing completed"
                    )

                    # Wait for the configured interval before next run
                    self.stop_flag.wait(self.config.process_interval)

                except Exception as e:
                    self.logger.error(f"Error in pipeline execution: {str(e)}")
                    self.monitor.update_state(
                        self.config.name,
                        PipelineStatus.ERROR,
                        error_message=str(e)
                    )
                    # Wait a bit before retrying after an error
                    self.stop_flag.wait(self.config.idle_time)

    def start(self):
        """Start the pipeline in a daemon thread"""
        if self.thread and self.thread.is_alive():
            raise RuntimeError(f"Pipeline {self.config.name} is already running")

        self.stop_flag.clear()
        self.thread = threading.Thread(
            target=self._run_pipeline,
            name=f"pipeline-{self.config.name}",
            daemon=True
        )
        self.thread.start()
        self.logger.info(f"Started pipeline: {self.config.name}")

    def stop(self):
        """Stop the pipeline gracefully"""
        self.stop_flag.set()
        if self.thread:
            self.thread.join(timeout=30)  # Wait up to 30 seconds
        self.monitor.update_state(
            self.config.name,
            PipelineStatus.STOPPED,
            "Pipeline stopped"
        )
        self.logger.info(f"Stopped pipeline: {self.config.name}")