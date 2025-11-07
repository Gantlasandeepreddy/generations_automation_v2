from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from db.database import get_db
from db import crud, models
from core.auth import require_admin

router = APIRouter(prefix="/api/users", tags=["users"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"  # "admin" or "user"


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


# ============================================================================
# USER MANAGEMENT ENDPOINTS (Admin Only)
# ============================================================================

@router.get("", response_model=List[UserResponse])
def get_users(
    include_inactive: bool = False,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only).

    Query params:
        include_inactive: Include inactive users (default: false)

    Response:
        [
            {
                "id": 1,
                "email": "user@example.com",
                "role": "admin",
                "is_active": true,
                "created_at": "2025-11-06T17:00:00"
            },
            ...
        ]
    """
    users = crud.get_all_users(db, include_inactive=include_inactive)

    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).

    Request body:
        {
            "email": "newuser@example.com",
            "password": "password123",
            "role": "user"  # or "admin"
        }

    Response:
        {
            "id": 2,
            "email": "newuser@example.com",
            "role": "user",
            "is_active": true,
            "created_at": "2025-11-06T17:00:00"
        }
    """
    # Check if email already exists
    existing_user = crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role
    if user_data.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'user'"
        )

    # Create user
    user = crud.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat()
    }


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only).

    Path params:
        user_id: ID of user to update

    Request body:
        {
            "email": "updated@example.com",  # optional
            "role": "admin",  # optional
            "is_active": false  # optional
        }

    Response:
        {
            "id": 2,
            "email": "updated@example.com",
            "role": "admin",
            "is_active": false,
            "created_at": "2025-11-06T17:00:00"
        }
    """
    # Get user to update
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate role if provided
    if user_data.role and user_data.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'user'"
        )

    # Check if email is already taken by another user
    if user_data.email and user_data.email != user.email:
        existing = crud.get_user_by_email(db, user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

    # Update user
    update_data = user_data.model_dump(exclude_unset=True)
    updated_user = crud.update_user(db, user_id, **update_data)

    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "role": updated_user.role,
        "is_active": updated_user.is_active,
        "created_at": updated_user.created_at.isoformat()
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Soft delete user (set is_active=False) (admin only).

    Path params:
        user_id: ID of user to delete

    Response:
        204 No Content
    """
    # Prevent admin from deleting themselves
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Check if user exists
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete
    success = crud.delete_user(db, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

    return None


@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Reset user password (admin only).

    Path params:
        user_id: ID of user whose password to reset

    Request body:
        {
            "new_password": "newpassword123"
        }

    Response:
        {
            "message": "Password reset successfully"
        }
    """
    # Check if user exists
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    crud.update_user(db, user_id, password=password_data.new_password)

    return {"message": "Password reset successfully"}
