from pydantic import BaseModel, EmailStr


class ValidateCredentialsRequest(BaseModel):
    agency_id: str
    email: EmailStr
    password: str


class SubmitJobRequest(BaseModel):
    agency_id: str
    email: EmailStr
    password: str
    start_date: str  # Format: MM/DD/YYYY
    end_date: str    # Format: MM/DD/YYYY
    client_limit: int = 10  # Default 10 clients per batch
