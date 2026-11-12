"""Authentication endpoints."""
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from api.deps import get_database
from core.security import create_access_token, decode_token, generate_user_id
from core.config import OAUTH_SESSION_URL, IS_PRODUCTION
from core.limiter import limiter
from models.user import UserCreate, UserLogin, create_user, authenticate_user, get_user_by_id, upsert_google_user

router = APIRouter(prefix="/auth", tags=["auth"])


class SessionRequest(BaseModel):
    session_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, response: Response):
    """Register a new user with email/password."""
    db = await get_database()
    try:
        user = await create_user(db, user_data)
        token = create_access_token(user['user_id'], user['email'])

        # Set httpOnly cookie so the token is not accessible to JavaScript
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="lax" if not IS_PRODUCTION else "none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )

        return {
            'access_token': token,
            'token_type': 'bearer',
            'user': user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin, response: Response):
    """Login with email/password."""
    db = await get_database()
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user['user_id'], user['email'])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax" if not IS_PRODUCTION else "none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {
        'access_token': token,
        'token_type': 'bearer',
        'user': user
    }


# REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
@router.post("/session")
@limiter.limit("10/minute")
async def process_session(request: Request, session_req: SessionRequest, response: Response):
    """Process session_id from OAuth callback."""
    if not OAUTH_SESSION_URL:
        raise HTTPException(status_code=503, detail="OAuth not configured")
    try:
        # Exchange session_id for user data
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                OAUTH_SESSION_URL,
                headers={"X-Session-ID": session_req.session_id},
                timeout=10.0
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            google_user = resp.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Auth service error: {str(e)}")
    
    # Upsert user in database
    db = await get_database()
    user = await upsert_google_user(db, google_user)
    
    # Create JWT token
    token = create_access_token(user['user_id'], user['email'])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax" if not IS_PRODUCTION else "none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {
        'access_token': token,
        'token_type': 'bearer',
        'user': user
    }


@router.get("/me")
async def get_me(request: Request):
    """Get current user from session."""
    # Check cookie first
    session_token = request.cookies.get('session_token')
    token = None
    
    if session_token:
        token = session_token
    else:
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_token(token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = await get_database()
    user = await get_user_by_id(db, payload['user_id'])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/logout")
async def logout(response: Response):
    """Logout and clear session."""
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=IS_PRODUCTION,
        samesite="lax" if not IS_PRODUCTION else "none"
    )
    return {"message": "Logged out successfully"}
