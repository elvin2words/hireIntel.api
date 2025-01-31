from enum import Enum


class PipelineStatus(Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    IDLE = "idle"
    RUNNING = "running"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"