from fastapi import APIRouter, HTTPException
from models.requests import ValidateCredentialsRequest
from models.responses import ValidateCredentialsResponse
from core.security import create_access_token
import tempfile
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/validate", response_model=ValidateCredentialsResponse)
def validate_credentials(request: ValidateCredentialsRequest):
    """
    Validate Generations credentials by attempting login.
    Returns JWT token if successful.
    """
    temp_dir = tempfile.mkdtemp()
    driver = None

    try:
        from automation import selenium_helpers
        from automation.report_automation import login_and_open_report_writer

        driver = selenium_helpers.build_driver(temp_dir, "validate", headless=True)
        login_and_open_report_writer(
            driver,
            request.agency_id,
            request.email,
            request.password
        )

        # If we got here, login succeeded
        token = create_access_token({"email": request.email})

        return ValidateCredentialsResponse(
            success=True,
            token=token,
            message="Credentials validated successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {str(e)}")

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
