# pipeline_manager.py

from typing import Dict, Optional
import logging
from flask import Flask

from src.PipeLines.PipeLineManagement.PipeLineBase import BasePipeline


class PipelineManager:
    def __init__(self, app: Flask):
        self.app = app
        self.pipelines: Dict[str, BasePipeline] = {}
        self.logger = logging.getLogger("pipeline.manager")

    def register_pipeline(self, pipeline: BasePipeline):
        """Register a new pipeline"""
        if pipeline.config.name in self.pipelines:
            raise ValueError(f"Pipeline {pipeline.config.name} already registered")

        self.pipelines[pipeline.config.name] = pipeline
        self.logger.info(f"Registered pipeline: {pipeline.config.name}")

    def start_all(self):
        """Start all registered pipelines"""
        for name, pipeline in self.pipelines.items():
            try:
                pipeline.start()
            except Exception as e:
                self.logger.error(f"Failed to start pipeline {name}: {str(e)}")

    def stop_all(self):
        """Stop all registered pipelines"""
        for name, pipeline in self.pipelines.items():
            try:
                pipeline.stop()
            except Exception as e:
                self.logger.error(f"Failed to stop pipeline {name}: {str(e)}")

    def get_pipeline(self, name: str) -> Optional[BasePipeline]:
        """Get a specific pipeline by name"""
        return self.pipelines.get(name)