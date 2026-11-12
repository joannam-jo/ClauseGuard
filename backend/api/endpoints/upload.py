"""Upload endpoints for PDF documents."""
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse

from api.deps import get_database, get_required_user
from core.config import UPLOAD_DIR
from models.document import DocumentCreate, create_document, compute_file_hash, get_document
from services.pdf_service import extract_text_from_bytes
from services.rag_service import prepare_document_for_rag
from ml.document_classifier import classify_document_type

router = APIRouter(prefix="/upload", tags=["upload"])

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_MIN_TEXT_LENGTH = 50


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _read_file_bytes(file: UploadFile) -> bytes:
    """Read and basic-validate uploaded file bytes."""
    try:
        data = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error reading file: {exc}") from exc
    return data


def _validate_file(filename: str, file_bytes: bytes) -> None:
    """Raise HTTPException for unsupported type, empty, or oversized files."""
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")


def _extract_text(file_bytes: bytes) -> tuple:
    """Extract text from PDF bytes; raise HTTPException on failure."""
    try:
        text, page_count = extract_text_from_bytes(file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {exc}") from exc
    if not text or len(text) < _MIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Please ensure it's not a scanned image.",
        )
    return text, page_count


async def _persist_file(file_path: Path, file_bytes: bytes) -> None:
    """Write file bytes to *file_path* on disk."""
    async with aiofiles.open(file_path, 'wb') as fh:
        await fh.write(file_bytes)


async def _prepare_rag(document_id: str, text: str) -> int:
    """Run RAG preparation and return chunk count (0 on failure)."""
    try:
        result = await prepare_document_for_rag(document_id, text)
        return result['chunk_count']
    except Exception as exc:
        print(f"Warning: RAG preparation failed: {exc}")
        return 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload a PDF document for analysis."""
    file_bytes = await _read_file_bytes(file)
    _validate_file(file.filename, file_bytes)

    extracted_text, page_count = _extract_text(file_bytes)
    content_hash = compute_file_hash(file_bytes)

    doc_type_result = classify_document_type(extracted_text[:5000])
    document_type = doc_type_result['type']

    user = await get_required_user(request)
    user_id = user['user_id']

    file_path = UPLOAD_DIR / f"{content_hash}.pdf"
    await _persist_file(file_path, file_bytes)

    db = await get_database()
    doc_data = DocumentCreate(
        filename=file.filename,
        file_size=len(file_bytes),
        content_hash=content_hash,
        page_count=page_count,
        extracted_text=extracted_text,
        document_type=document_type,
    )
    document = await create_document(db, doc_data, user_id)
    document['chunk_count'] = await _prepare_rag(document['document_id'], extracted_text)

    return {
        'success': True,
        'document': document,
        'document_type_confidence': doc_type_result['confidence'],
    }


@router.get("/{document_id}/file")
async def get_document_file(document_id: str):
    """Return the original PDF file for a document."""
    db = await get_database()
    document = await get_document(db, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = UPLOAD_DIR / f"{document['content_hash']}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        media_type='application/pdf',
        filename=document['filename'],
    )
