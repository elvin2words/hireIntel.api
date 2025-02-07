import json
import math
import time
from datetime import datetime, timezone

from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required

from src.Helpers.Response import apiResponse
from src.Modules.Candidate.CandidateService import CandidateService
from src.Modules.Interviews.InterviewServices import InterviewSchedulerService
from src.Modules.Jobs.JobService import JobService

ADMIN_CONTROLLER = Blueprint('admin_controller', __name__, url_prefix='/api/v1/admin')
jobService = JobService()
interviewService = InterviewSchedulerService()
candidateService = CandidateService()


#====================================
# Job Management Endpoints
#====================================

@ADMIN_CONTROLLER.route('/jobs', methods=['GET'])
@jwt_required()
def get_all_jobs():
    filters = request.args.to_dict()
    jobs = jobService.fetch_all(filters)
    return apiResponse(False, 200, jobs, "Jobs fetched successfully")


@ADMIN_CONTROLLER.route('/jobs/<string:job_id>', methods=['GET'])
@jwt_required()
def get_job_by_id(job_id: str):
    job = jobService.fetch_by_id(job_id)
    return apiResponse(False, 200, job, "Job fetched successfully")


@ADMIN_CONTROLLER.route('/jobs', methods=['POST'])
@jwt_required()
def create_job():
    data = request.get_json()
    job = jobService.create_job(data)
    return apiResponse(False, 201, job, "Job created successfully")


@ADMIN_CONTROLLER.route('/jobs/<string:job_id>', methods=['PUT'])
@jwt_required()
def update_job(job_id: str):
    data = request.get_json()
    job = jobService.update_job(job_id, data)
    return apiResponse(False, 200, job, "Job updated successfully")


@ADMIN_CONTROLLER.route('/jobs/<string:job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id: str):
    jobService.delete_job(job_id)
    return apiResponse(False, 200, None, "Job deleted successfully")


@ADMIN_CONTROLLER.route('/jobs/<string:job_id>/publish', methods=['POST'])
@jwt_required()
def publish_job(job_id: str):
    job = jobService.publish_job(job_id)
    return apiResponse(False, 200, job, "Job published successfully")


@ADMIN_CONTROLLER.route('/jobs/<string:job_id>/close', methods=['POST'])
@jwt_required()
def close_job(job_id: str):
    job = jobService.close_job(job_id)
    return apiResponse(False, 200, job, "Job closed successfully")


#====================================
# Interview Scheduling Endpoints
#====================================

@ADMIN_CONTROLLER.route('/interviews/schedule', methods=['POST'])
# @jwt_required()
def schedule_interviews():
    """Schedule interviews for multiple candidates"""
    data = request.get_json()
    print("the json data is : ", data)
    result = interviewService.process_candidates(data)
    return apiResponse(
        False,
        201,
        result,
        "Interview schedules created successfully"
    )


@ADMIN_CONTROLLER.route('/interviews/schedules', methods=['GET'])
@jwt_required()
def get_interview_schedules():
    """Get all interview schedules with optional filtering"""
    filters = request.args.to_dict()
    schedules = interviewService.get_all_schedules(filters)
    return apiResponse(
        False,
        200,
        schedules,
        "Interview schedules fetched successfully"
    )


@ADMIN_CONTROLLER.route('/interviews/schedules/<string:schedule_id>', methods=['GET'])
@jwt_required()
def get_interview_schedule(schedule_id: str):
    """Get specific interview schedule by ID"""
    schedule = interviewService.get_schedule_by_id(schedule_id)
    return apiResponse(
        False,
        200,
        schedule,
        "Interview schedule fetched successfully"
    )


@ADMIN_CONTROLLER.route('/interviews/schedules/<string:schedule_id>', methods=['PUT'])
@jwt_required()
def update_interview_schedule(schedule_id: str):
    """Update an existing interview schedule"""
    data = request.get_json()
    schedule = interviewService.update_schedule(schedule_id, data)
    return apiResponse(
        False,
        200,
        schedule,
        "Interview schedule updated successfully"
    )


@ADMIN_CONTROLLER.route('/interviews/schedules/<string:schedule_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_interview(schedule_id: str):
    """Cancel a scheduled interview"""
    schedule = interviewService.cancel_schedule(schedule_id)
    return apiResponse(
        False,
        200,
        schedule,
        "Interview schedule cancelled successfully"
    )


@ADMIN_CONTROLLER.route('/interviews/schedules/<string:schedule_id>/complete', methods=['POST'])
@jwt_required()
def complete_interview(schedule_id: str):
    """Mark an interview as completed"""
    schedule = interviewService.complete_schedule(schedule_id)
    return apiResponse(
        False,
        200,
        schedule,
        "Interview schedule marked as completed successfully"
    )


# ====================================
# Candidate Monitoring Endpoints
# ====================================

def paginate_data(data, page, per_page):
    """Paginate the candidates data"""
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return {
        "items": data[start_idx:end_idx],
        "total": len(data),
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(len(data) / per_page)
    }


def format_monitor_data(candidates_data, page=1, per_page=10):
    """Format the monitor data with proper structure and pagination"""
    paginated_data = paginate_data(candidates_data, page, per_page)

    return {
        "error": False,
        "data": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidates": paginated_data["items"],
            "pagination": {
                "total": paginated_data["total"],
                "page": paginated_data["page"],
                "per_page": paginated_data["per_page"],
                "total_pages": paginated_data["total_pages"]
            }
        },
        "msg": "Candidates status updated"
    }


@ADMIN_CONTROLLER.route('/candidates/stream', methods=['GET'])
# @jwt_required()  # Uncomment after testing
def stream_candidates_status():
    """Stream candidates status updates using Server-Sent Events with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    def generate():
        while True:
            try:
                # Get the current page from query parameter
                current_page = request.args.get('page', page, type=int)

                # Fetch current candidates data
                candidates = candidateService.fetch_all()

                # Format the response data with pagination
                monitor_data = format_monitor_data(
                    candidates,
                    page=current_page,
                    per_page=per_page
                )

                # Send the event
                yield f"data: {json.dumps(monitor_data)}\n\n"

                # Wait before next update
                time.sleep(1)

            except Exception as e:
                error_data = {
                    "error": True,
                    "data": None,
                    "msg": f"Error fetching candidates: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                time.sleep(5)  # Wait longer on error

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Content-Type': 'text/event-stream',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

# def format_monitor_data(candidates_data):
#     """Format the monitor data with proper structure"""
#     return {
#         "error": False,
#         "data": {
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "candidates": candidates_data,
#             "total": len(candidates_data)
#         },
#         "msg": "Candidates status updated"
#     }
#
#
# @ADMIN_CONTROLLER.route('/candidates/stream', methods=['GET'])
# # @jwt_required()  # Uncomment after testing
# def stream_candidates_status():
#     """Stream candidates status updates using Server-Sent Events"""
#
#     def generate():
#         while True:
#             try:
#                 # Fetch current candidates data
#                 candidates = candidateService.fetch_all()
#
#                 # Format the response data
#                 monitor_data = format_monitor_data(candidates)
#
#                 # Send the event
#                 yield f"data: {json.dumps(monitor_data)}\n\n"
#
#                 # Wait before next update
#                 time.sleep(1)
#
#             except Exception as e:
#                 error_data = {
#                     "error": True,
#                     "data": None,
#                     "msg": f"Error fetching candidates: {str(e)}",
#                     "timestamp": datetime.now(timezone.utc).isoformat()
#                 }
#                 yield f"data: {json.dumps(error_data)}\n\n"
#                 time.sleep(5)  # Wait longer on error
#
#     return Response(
#         stream_with_context(generate()),
#         mimetype='text/event-stream',
#         headers={
#             'Cache-Control': 'no-cache',
#             'Content-Type': 'text/event-stream',
#             'Connection': 'keep-alive',
#             'X-Accel-Buffering': 'no'
#         }
#     )