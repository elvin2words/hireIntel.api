from flask import Flask
import atexit

from src.Modules.Profiling.ProfilerCoordinator import MonitoredProfilerCoordinator
from src.config.ConfigBase import Config
from src.config.PipeLineMonitorDecl import pipelineMonitor


class ProfilerConfig:
    def __init__(self, config):
        """Initialize profiler configuration from config.yaml"""
        self.github_token = config.getConfig()["profiler"]["github_token"]
        self.google_api_key = config.getConfig()["profiler"]["google_api_key"]
        self.intervals = config.getConfig()["profiler"]["intervals"]

def init_profiler(app: Flask, config: Config) -> MonitoredProfilerCoordinator:
    """Initialize the profiler system"""
    profiler_config = ProfilerConfig(config)

    profiler = MonitoredProfilerCoordinator(
        github_token=profiler_config.github_token,
        google_api_key=profiler_config.google_api_key,
        monitor=pipelineMonitor
    )

    # Update intervals if specified in config
    profiler.intervals.update(profiler_config.intervals)

    # Register cleanup on application shutdown
    atexit.register(profiler.stop_scheduling)

    return profiler