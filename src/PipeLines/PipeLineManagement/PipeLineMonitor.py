# pipeline_monitor.py

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import logging

from src.PipeLines.PipeLineManagement.PipeLineModels import PipelineStatus


@dataclass
class PipelineState:
    status: PipelineStatus
    message: str
    error_message: Optional[str]
    last_updated: datetime
    details: Dict[str, Any]


class PipelineMonitor:
    def __init__(self):
        self._states: Dict[str, PipelineState] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger("pipeline.monitor")

    def update_state(
            self,
            pipeline_name: str,
            status: PipelineStatus,
            message: str = "",
            error_message: Optional[str] = None,
            details: Dict[str, Any] = None
    ):
        """Thread-safe state update"""
        with self._lock:
            self._states[pipeline_name] = PipelineState(
                status=status,
                message=message,
                error_message=error_message,
                last_updated=datetime.utcnow(),
                details=details or {}
            )
        self.logger.info(
            f"Pipeline {pipeline_name} state updated: {status.value} - {message}"
        )

    def get_state(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a specific pipeline"""
        with self._lock:
            state = self._states.get(pipeline_name)
            if not state:
                return None

            return {
                "status": state.status.value,
                "message": state.message,
                "error_message": state.error_message,
                "last_updated": state.last_updated.isoformat(),
                "details": state.details
            }

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all registered pipelines"""
        with self._lock:
            return {
                name: {
                    "status": state.status.value,
                    "message": state.message,
                    "error_message": state.error_message,
                    "last_updated": state.last_updated.isoformat(),
                    "details": state.details
                }
                for name, state in self._states.items()
            }