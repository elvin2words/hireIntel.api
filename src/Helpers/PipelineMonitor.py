from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

class PipelineStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DOWN = "down"

class PipelineState:
    def __init__(self):
        self.status: PipelineStatus = PipelineStatus.IDLE
        self.message: str = ""
        self.error_message: Optional[str] = None
        self.last_updated: datetime = datetime.utcnow()
        self.details: Dict[str, Any] = {}

class PipelineMonitor:
    def __init__(self):
        self._pipeline_states: Dict[str, PipelineState] = {}

    def update_pipeline_state(
        self,
        pipeline_name: str,
        status: PipelineStatus,
        message: str = "",
        error_message: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        if pipeline_name not in self._pipeline_states:
            self._pipeline_states[pipeline_name] = PipelineState()

        state = self._pipeline_states[pipeline_name]
        state.status = status
        state.message = message
        state.error_message = error_message
        state.last_updated = datetime.utcnow()
        state.details = details or {}

    def get_pipeline_state(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        state = self._pipeline_states.get(pipeline_name)
        if not state:
            return None

        return {
            "status": state.status.value,
            "message": state.message,
            "error_message": state.error_message,
            "last_updated": state.last_updated.isoformat(),
            "details": state.details
        }

    def get_all_pipeline_states(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "status": state.status.value,
                "message": state.message,
                "error_message": state.error_message,
                "last_updated": state.last_updated.isoformat(),
                "details": state.details
            }
            for name, state in self._pipeline_states.items()
        }