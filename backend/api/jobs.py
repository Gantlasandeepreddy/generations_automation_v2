from fastapi import APIRouter, HTTPException, Depends
from models.requests import SubmitJobRequest
from models.responses import SubmitJobResponse, JobStatusResponse
from core.security import get_current_user
from db import crud
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/submit", response_model=SubmitJobResponse)
def submit_job(request: SubmitJobRequest, user=Depends(get_current_user)):
    """
    Submit automation job to queue.
    Job will be processed by Huey worker in background.
    """
    job_id = str(uuid.uuid4())

    # Create job record
    crud.create_job(
        job_id=job_id,
        user_email=user['email'],
        date_range_start=request.start_date,
        date_range_end=request.end_date
    )

    # Queue job (import here to avoid circular dependency)
    from workers.tasks import run_automation_job

    # CRITICAL: Must call with () to enqueue the task
    run_automation_job(
        job_id,
        {
            'agency_id': request.agency_id,
            'email': request.email,
            'password': request.password
        },
        {
            'start': request.start_date,
            'end': request.end_date,
            'client_limit': request.client_limit
        }
    )  # This actually enqueues the task to Huey

    return SubmitJobResponse(
        job_id=job_id,
        status="queued",
        message="Job submitted successfully"
    )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    Poll job status.
    Frontend should call this endpoint every 3 seconds during processing.
    """
    job = crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        total_clients=job['total_clients'] or 0,
        processed_clients=job['processed_clients'] or 0,
        failed_clients=job['failed_clients'] or 0,
        logs=job['logs'] or '',
        created_at=job['created_at'],
        completed_at=job['completed_at'],
        error_message=job['error_message']
    )


@router.delete("/{job_id}/cancel")
def cancel_job(job_id: str, user=Depends(get_current_user)):
    """
    Cancel a running or queued job.
    Note: Currently running jobs may not stop immediately.
    """
    job = crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job['status'] in ['completed', 'failed']:
        raise HTTPException(status_code=400, detail="Job already finished")

    crud.fail_job(job_id, "Cancelled by user")
    return {"message": "Job cancelled"}
