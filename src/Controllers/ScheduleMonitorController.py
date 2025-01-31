from flask import Blueprint, jsonify, current_app, Response, stream_with_context
from datetime import datetime, timezone
import json
import time

MONITOR_CONTROLLER = Blueprint('monitor', __name__)


def get_monitor():
    if not hasattr(current_app, 'pipeline_monitor'):
        raise RuntimeError("Pipeline monitor not initialized")
    return current_app.pipeline_monitor


def get_manager():
    if not hasattr(current_app, 'pipeline_manager'):
        raise RuntimeError("Pipeline manager not initialized")
    return current_app.pipeline_manager


def get_pipeline_metrics(pipeline):
    monitor = get_monitor()
    state = monitor.get_state(pipeline.config.name)
    if not state:
        return {}

    thread = pipeline.thread
    return {
        "name": pipeline.config.name,
        "status": state["status"],
        "last_updated": state["last_updated"],
        "message": state["message"],
        "error_message": state["error_message"],
        "thread_info": {
            "is_alive": thread.is_alive() if thread else False,
            "thread_id": thread.ident if thread else None,
            "thread_name": thread.name if thread else None
        }
    }


@MONITOR_CONTROLLER.route('/api/monitor/status/stream', methods=['GET'])
def stream_status():
    """Stream pipeline status updates using Server-Sent Events"""

    def generate():
        while True:
            try:
                pipeline_manager = get_manager()
                status = {
                    name: get_pipeline_metrics(pipeline)
                    for name, pipeline in pipeline_manager.pipelines.items()
                }

                data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pipelines": status
                }

                # Format as SSE data
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(1)  # Send updates every second

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(5)  # Wait longer on error

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # Disable proxy buffering
            'Access-Control-Allow-Origin': '*'
        }
    )


@MONITOR_CONTROLLER.route('/api/monitor/status', methods=['GET'])
def get_pipeline_status():
    """Get current status of all pipelines"""
    try:
        pipeline_manager = get_manager()
        status = {
            name: get_pipeline_metrics(pipeline)
            for name, pipeline in pipeline_manager.pipelines.items()
        }

        return jsonify({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipelines": status
        })
    except Exception as e:
        return jsonify({
            "error": "Status check failed",
            "message": str(e)
        }), 500