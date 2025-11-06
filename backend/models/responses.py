from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ValidateCredentialsResponse(BaseModel):
    success: bool
    token: str
    message: str


class SubmitJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    total_clients: int
    processed_clients: int
    failed_clients: int
    logs: str
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
