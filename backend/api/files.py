from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from db import crud
import os

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/{job_id}/download")
def download_file(job_id: str):
    """
    Download final Excel file for completed job.
    Returns file stream for browser download.
    """
    job = crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Job not completed yet (status: {job['status']})")

    file_path = job['excel_file_path']
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    filename = os.path.basename(file_path)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.get("/{job_id}/preview")
def preview_json(job_id: str):
    """
    Preview JSON data for completed job.
    Useful for debugging or viewing raw data.
    """
    job = crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    json_path = job['json_file_path']
    if not json_path or not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="JSON file not found")

    import json
    with open(json_path, 'r') as f:
        data = json.load(f)

    return {"total_records": len(data), "data": data[:10]}  # Return first 10 records for preview
