"""Chat endpoints for document Q&A."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List

from api.deps import get_database, get_required_user
from models.document import get_document
from services.rag_service import build_rag_context
from services.llm_service import chat_with_document

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    document_id: str
    message: str
    history: Optional[List[ChatMessage]] = None


@router.post("")
async def chat(req: ChatRequest, request: Request):
    """Chat with a document using RAG."""
    db = await get_database()
    user = await get_required_user(request)
    
    # Get document
    document = await get_document(db, req.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get('user_id') != user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Build RAG context
    context = await build_rag_context(req.document_id, req.message, n_results=5)
    
    # Format history
    history = None
    if req.history:
        history = [{'role': m.role, 'content': m.content} for m in req.history]
    
    # Get response
    try:
        response = await chat_with_document(
            req.document_id,
            req.message,
            context,
            history
        )
        
        return {
            'success': True,
            'response': response,
            'context_used': len(context) > 100
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/search")
async def search_document(document_id: str, query: str, request: Request):
    """Search within a document using semantic search."""
    db = await get_database()
    user = await get_required_user(request)
    
    # Get document
    document = await get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get('user_id') != user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from services.vector_store import query_document_async
    
    results = await query_document_async(document_id, query, n_results=10)
    
    return {
        'success': True,
        'results': results
    }
