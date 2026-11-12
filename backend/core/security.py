"""Security utilities for authentication."""
import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from core.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: str, email: str) -> str:
    """Create a JWT access token."""
    expires = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': expires,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')


def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{uuid.uuid4().hex[:12]}"


def generate_document_id() -> str:
    """Generate a unique document ID."""
    return f"doc_{uuid.uuid4().hex[:12]}"


def generate_analysis_id() -> str:
    """Generate a unique analysis ID."""
    return f"analysis_{uuid.uuid4().hex[:12]}"


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Get current user from token (optional - returns None if not authenticated)."""
    # Check cookie first
    session_token = request.cookies.get('session_token')
    if session_token:
        try:
            return decode_token(session_token)
        except Exception:
            pass

    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            return decode_token(token)
        except Exception:
            pass
    
    return None


async def get_current_user(request: Request) -> dict:
    """Get current user from token (required)."""
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail='Not authenticated')
    return user
