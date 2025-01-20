# src/routes/monitor.py
from flask import Blueprint, jsonify
from src.Helpers.PipelineMonitor import PipelineMonitor
from src.config.PipeLineMonitorDecl import pipelineMonitor

MONITOR_CONTROLLER = Blueprint('monitor', __name__)

@MONITOR_CONTROLLER.route('/api/monitor/status', methods=['GET'])
def get_pipeline_status():
    """Get status of all pipelines"""
    return jsonify(pipelineMonitor.get_all_pipeline_states())

@MONITOR_CONTROLLER.route('/api/monitor/status/<pipeline_name>', methods=['GET'])
def get_specific_pipeline_status(pipeline_name):
    """Get status of a specific pipeline"""
    state = pipelineMonitor.get_pipeline_state(pipeline_name)
    if state is None:
        return jsonify({"error": "Pipeline not found"}), 404
    return jsonify(state)