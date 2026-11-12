"""User model and database operations."""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.security import generate_user_id, hash_password, verify_password


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain an uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a digit')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime
    auth_provider: str = 'email'  # email or google


class UserInDB(User):
    password_hash: Optional[str] = None


def serialize_user(user_doc: dict) -> dict:
    """Serialize user document for API response."""
    if '_id' in user_doc:
        del user_doc['_id']
    if 'password_hash' in user_doc:
        del user_doc['password_hash']
    if isinstance(user_doc.get('created_at'), datetime):
        user_doc['created_at'] = user_doc['created_at'].isoformat()
    return user_doc


async def create_user(db: AsyncIOMotorDatabase, user_data: UserCreate) -> dict:
    """Create a new user with email/password."""
    existing = await db.users.find_one({'email': user_data.email})
    if existing:
        raise ValueError('Email already registered')
    
    user_id = generate_user_id()
    user_doc = {
        'user_id': user_id,
        'email': user_data.email,
        'name': user_data.name,
        'password_hash': hash_password(user_data.password),
        'picture': None,
        'created_at': datetime.now(timezone.utc),
        'auth_provider': 'email'
    }
    
    await db.users.insert_one(user_doc)
    return serialize_user(user_doc.copy())


async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[dict]:
    """Authenticate user with email/password."""
    user_doc = await db.users.find_one({'email': email}, {'_id': 0})
    if not user_doc:
        return None
    
    if not user_doc.get('password_hash'):
        return None  # OAuth user, can't login with password
    
    if not verify_password(password, user_doc['password_hash']):
        return None
    
    return serialize_user(user_doc.copy())


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    """Get user by ID."""
    user_doc = await db.users.find_one({'user_id': user_id}, {'_id': 0})
    if user_doc:
        return serialize_user(user_doc.copy())
    return None


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    """Get user by email."""
    user_doc = await db.users.find_one({'email': email}, {'_id': 0})
    if user_doc:
        return serialize_user(user_doc.copy())
    return None


async def upsert_google_user(db: AsyncIOMotorDatabase, google_user: dict) -> dict:
    """Create or update user from Google OAuth."""
    email = google_user['email']
    existing = await db.users.find_one({'email': email})
    
    if existing:
        # Update existing user
        await db.users.update_one(
            {'email': email},
            {'$set': {
                'name': google_user.get('name', existing.get('name')),
                'picture': google_user.get('picture')
            }}
        )
        updated = await db.users.find_one({'email': email}, {'_id': 0})
        return serialize_user(updated.copy())
    
    # Create new user
    user_id = generate_user_id()
    user_doc = {
        'user_id': user_id,
        'email': email,
        'name': google_user.get('name', email.split('@')[0]),
        'picture': google_user.get('picture'),
        'created_at': datetime.now(timezone.utc),
        'auth_provider': 'google'
    }
    
    await db.users.insert_one(user_doc)
    return serialize_user(user_doc.copy())
