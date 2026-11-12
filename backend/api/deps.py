"""API dependencies."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Request, HTTPException
from typing import Optional
from pymongo import server_api

from core.config import MONGO_URL, DB_NAME
from core.security import get_current_user, get_current_user_optional

# Global database client - with type hints for clarity
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get database connection."""
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URL, server_api=server_api.ServerApi('1'))
        _db = _client[DB_NAME]
    return _db


async def get_optional_user(request: Request) -> Optional[dict]:
    """Get current user if authenticated (optional)."""
    return await get_current_user_optional(request)


async def get_required_user(request: Request) -> dict:
    """Get current user (required)."""
    return await get_current_user(request)
