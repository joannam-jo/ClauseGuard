"""Document model and database operations."""
import hashlib
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.security import generate_document_id


class DocumentCreate(BaseModel):
    filename: str
    file_size: int
    content_hash: str
    page_count: int
    extracted_text: str
    document_type: str  # loan, lease, credit_card, unknown


class Document(BaseModel):
    document_id: str
    user_id: Optional[str] = None  # None for guest uploads
    filename: str
    file_size: int
    content_hash: str
    page_count: int
    extracted_text: str
    document_type: str
    status: str  # uploaded, processing, analyzed, error
    created_at: datetime
    analyzed_at: Optional[datetime] = None


def serialize_document(doc: dict) -> dict:
    """Serialize document for API response."""
    if '_id' in doc:
        del doc['_id']
    for field in ['created_at', 'analyzed_at']:
        if isinstance(doc.get(field), datetime):
            doc[field] = doc[field].isoformat()
    return doc


async def create_document(db: AsyncIOMotorDatabase, doc_data: DocumentCreate, user_id: Optional[str] = None) -> dict:
    """Create a new document record."""
    document_id = generate_document_id()
    doc = {
        'document_id': document_id,
        'user_id': user_id,
        'filename': doc_data.filename,
        'file_size': doc_data.file_size,
        'content_hash': doc_data.content_hash,
        'page_count': doc_data.page_count,
        'extracted_text': doc_data.extracted_text,
        'document_type': doc_data.document_type,
        'status': 'uploaded',
        'created_at': datetime.now(timezone.utc),
        'analyzed_at': None
    }
    
    await db.documents.insert_one(doc)
    return serialize_document(doc.copy())


async def get_document(db: AsyncIOMotorDatabase, document_id: str) -> Optional[dict]:
    """Get document by ID."""
    doc = await db.documents.find_one({'document_id': document_id}, {'_id': 0})
    if doc:
        return serialize_document(doc.copy())
    return None


async def get_user_documents(db: AsyncIOMotorDatabase, user_id: str) -> List[dict]:
    """Get all documents for a user."""
    cursor = db.documents.find({'user_id': user_id}, {'_id': 0}).sort('created_at', -1)
    docs = await cursor.to_list(length=100)
    return [serialize_document(d.copy()) for d in docs]


async def update_document_status(db: AsyncIOMotorDatabase, document_id: str, status: str, analyzed_at: Optional[datetime] = None):
    """Update document status."""
    update = {'status': status}
    if analyzed_at:
        update['analyzed_at'] = analyzed_at
    await db.documents.update_one({'document_id': document_id}, {'$set': update})


async def delete_document(db: AsyncIOMotorDatabase, document_id: str):
    """Delete a document."""
    await db.documents.delete_one({'document_id': document_id})


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file content (cryptographically secure)."""
    return hashlib.sha256(file_bytes).hexdigest()
