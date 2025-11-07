from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from db.database import get_db
from db import models
from core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user
)
from core.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # 5 login attempts per minute per IP
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    Rate limited to 5 attempts per minute per IP address.

    Request body:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Response:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "role": "admin",
                "is_active": true
            }
        }
    """
    user = authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token_expires = timedelta(days=settings.jwt_expire_days)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    Get current authenticated user's information.

    Headers:
        Authorization: Bearer <token>

    Response:
        {
            "id": 1,
            "email": "user@example.com",
            "role": "admin",
            "is_active": true
        }
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: models.User = Depends(get_current_user)):
    """
    Refresh access token.
    Requires valid existing token.

    Headers:
        Authorization: Bearer <old_token>

    Response:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "user": {...}
        }
    """
    access_token_expires = timedelta(days=settings.jwt_expire_days)
    access_token = create_access_token(
        data={
            "sub": current_user.email,
            "user_id": current_user.id,
            "role": current_user.role
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "is_active": current_user.is_active
        }
    }
