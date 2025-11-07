from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from db.database import get_db
from db import crud, models

# JWT settings (will be overridden by config)
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION_USE_ENV_VARIABLE"  # Override in config.py
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# HTTP Bearer token scheme
security = HTTPBearer()


# ============================================================================
# PASSWORD HASHING
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


# ============================================================================
# JWT TOKEN OPERATIONS
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing token payload (usually {"sub": email, "user_id": id, "role": role})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ============================================================================
# AUTHENTICATION DEPENDENCIES FOR FASTAPI
# ============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Usage:
        @app.get("/api/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.email}"}

    Raises:
        HTTPException 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    FastAPI dependency to require admin role.

    Usage:
        @app.get("/api/admin/users")
        def admin_route(user: User = Depends(require_admin)):
            return {"message": "Admin access granted"}

    Raises:
        HTTPException 403 if user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


# ============================================================================
# AUTHENTICATION HELPER
# ============================================================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    Authenticate a user by email and password.

    Returns:
        User object if authentication successful, None otherwise
    """
    user = crud.get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user


def initialize_secret_key(secret_key: str):
    """Update SECRET_KEY from settings (called during app startup)"""
    global SECRET_KEY
    SECRET_KEY = secret_key
