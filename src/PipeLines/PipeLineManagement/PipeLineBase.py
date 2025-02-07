from abc import ABC, abstractmethod
from typing import Optional, Any
import threading
import logging
from flask import Flask
import colorlog

from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus


from abc import ABC, abstractmethod
from typing import Optional, Any
import threading
import logging
import colorlog

from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus
from src.PipeLines.PipeLineManagement.PipeLineMonitor import PipelineMonitor

# Create a lock for thread-safe logger configuration
logger_lock = threading.Lock()
configured_loggers = set()


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
    def __init__(self, app: Flask, config: PipelineConfig, monitor: PipelineMonitor):
        self.app = app
        self.config = config
        self.monitor = monitor
        self.thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()

        # Configure logging with thread safety
        with logger_lock:
            logger_name = f"pipeline.{config.name}"
            self.logger = logging.getLogger(logger_name)

            # Only configure if this logger hasn't been set up before
            if logger_name not in configured_loggers:
                # Clear any existing handlers
                self.logger.handlers.clear()

                # Configure the PROCESSING level if not already done
                if not hasattr(logging, 'PROCESSING'):
                    logging.addLevelName(25, 'PROCESSING')

                    def processing(self, message, *args, **kwargs):
                        if self.isEnabledFor(25):
                            self._log(25, message, args, **kwargs)

                    logging.Logger.processing = processing

                # Add single handler with color formatting
                handler = colorlog.StreamHandler()
                handler.setFormatter(colorlog.ColoredFormatter(
                    '%(log_color)s%(levelname)s:%(name)s:%(message)s',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'blue',
                        'PROCESSING': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                ))
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

                # Mark this logger as configured
                configured_loggers.add(logger_name)

    @abstractmethod
    def get_input_data(self) -> Any:
        """Retrieve input data for the pipeline"""
        pass

    @abstractmethod
    def process_item(self, item: Any) -> Any:
        """Process a single input item"""
        pass

    @abstractmethod
    def update_output(self, data: Any) -> None:
        """Persist the processed data"""
        pass

    @abstractmethod
    def handle_item_failure(self, item: Any, error: Exception) -> None:
        """Handle failure during item processing"""
        pass

    def process_batch(self) -> None:
        self.monitor.update_state(self.config.name, PipelineStatus.INPUT_FETCHED, "Fetching input data")
        input_data = self.get_input_data()

        self.monitor.update_state(self.config.name, PipelineStatus.PROCESSING_STARTED, "Processing data",
                                  details={'input_records': len(input_data)})

        processed_data = []
        for item in input_data:
            try:
                result = self.process_item(item)
                processed_data.append(result)
            except Exception as e:
                self.logger.exception(f"Error processing item {item}: {str(e)}")
                self.handle_item_failure(item, e)

        self.monitor.update_state(self.config.name, PipelineStatus.PROCESSING_COMPLETED, "Data processing completed",
                                  details={'output_records': len(processed_data)})

        self.monitor.update_state(self.config.name, PipelineStatus.OUTPUT_UPDATED, "Updating output")
        self.update_output(processed_data)

    def _run_pipeline(self):
        """Internal method to run the pipeline loop"""
        with self.app.app_context():
            while not self.stop_flag.is_set():
                try:
                    self.monitor.update_state(
                        self.config.name,
                        PipelineStatus.IDLE,
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
                    self.logger.exception(f"Error in pipeline execution: {str(e)}")
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
        # Log startup message only once
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
