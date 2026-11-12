"""Analysis endpoints."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from api.deps import get_database, get_required_user
from models.document import get_document, update_document_status, get_user_documents, delete_document
from models.analysis import create_analysis, get_document_analysis, delete_document_analyses
from services.llm_service import analyze_document, analyze_clauses_detailed
from services.chunking_service import chunk_text
from services.vector_store import delete_document_collection
from ml.clause_classifier import classify_clauses
from ml.risk_scorer import score_document_risk

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    document_id: str
    force_reanalyze: bool = False


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def _run_ml_risk_scoring(text: str) -> dict:
    """Run ML-based risk scoring on the document text."""
    return score_document_risk(text[:10000])


async def _run_llm_analysis(text: str, doc_type: str) -> dict:
    """Run full LLM document analysis."""
    return await analyze_document(text, doc_type)


async def _run_clause_analysis(text: str, doc_type: str) -> list:
    """Run detailed LLM clause analysis."""
    return await analyze_clauses_detailed(text[:15000], doc_type)


def _merge_ml_classifications(clauses: list) -> list:
    """Enrich clauses with ML-based predictions where confidence is higher."""
    if not clauses:
        return clauses

    clause_texts = [c.get('text', '')[:500] for c in clauses]
    ml_classifications = classify_clauses(clause_texts)

    for i, clause in enumerate(clauses):
        if i < len(ml_classifications):
            ml_pred = ml_classifications[i]
            if ml_pred['confidence'] > clause.get('confidence', 0):
                clause['ml_prediction'] = ml_pred['prediction']
                clause['ml_confidence'] = ml_pred['confidence']

    return clauses


def _generate_ml_clauses(text: str) -> list:
    """Generate clause objects from ML predictions when LLM is unavailable."""
    chunks = chunk_text(text[:15000], chunk_size=250, overlap=30, min_chunk_size=50)
    if not chunks:
        return []

    chunk_texts = [c['text'][:500] for c in chunks]
    predictions = classify_clauses(chunk_texts)

    clauses = []
    for i, (chunk, pred) in enumerate(zip(chunks, predictions)):
        if not chunk['text'].strip():
            continue

        title = chunk['text'][:80].split('.')[0].strip()[:60] or f"Clause {i+1}"
        risk_level = 'BENEFICIAL' if pred['prediction'] == 'beneficial' else 'HIGH'
        confidence = pred['confidence']

        clauses.append({
            'clause_id': str(uuid.uuid4())[:8],
            'title': title,
            'text': chunk['text'],
            'risk_level': risk_level,
            'category': pred['prediction'],
            'confidence': confidence,
            'risk_score': round((1 - confidence) * 10, 1) if pred['prediction'] == 'beneficial' else round(confidence * 10, 1),
            'explanation': f"ML classified as {pred['prediction']} (confidence: {confidence:.0%})",
        })

    return clauses


def _generate_fallback_checklist(clauses: list) -> list:
    """Generate basic checklist items from ML clause data."""
    items = []
    harmful = [c for c in clauses if c.get('category') == 'harmful']
    beneficial = [c for c in clauses if c.get('category') == 'beneficial']

    if harmful:
        items.append(f"Review {len(harmful)} potentially harmful clause(s) identified in the document")
        items.append("Consider negotiating or requesting removal of harmful terms")
    if beneficial:
        items.append(f"Benefit from {len(beneficial)} favorable clause(s) found in your favor")
    items.append("Document overall risk score should be reviewed")
    items.append("Seek legal advice if any terms are unclear")
    return items


def _generate_fallback_questions(clauses: list) -> list:
    """Generate basic questions from harmful clause data."""
    harmful = [c for c in clauses if c.get('category') == 'harmful']
    if not harmful:
        return ["Are there any hidden fees or charges not disclosed?"]

    questions = []
    for c in harmful[:5]:
        text = c.get('text', '')[:80]
        questions.append(f"Can you clarify the term regarding: '{text}...'")
    questions.append("Are there any penalties or fees I should be aware of?")
    return questions


def _generate_fallback_alternatives(clauses: list) -> list:
    """Generate basic alternatives from harmful clause data."""
    harmful = [c for c in clauses if c.get('category') == 'harmful']
    if not harmful:
        return ["Request a simplified version of the agreement with clearer terms"]

    alternatives = []
    for c in harmful[:3]:
        cat = c.get('category', 'harmful')
        if 'penalty' in c.get('text', '').lower():
            alternatives.append("Request removal or reduction of penalty clauses")
        elif 'waive' in c.get('text', '').lower():
            alternatives.append("Negotiate to retain your legal rights instead of waiving them")
        elif 'fee' in c.get('text', '').lower():
            alternatives.append("Ask for a detailed fee schedule and negotiate fee reductions")
    if not alternatives:
        alternatives.append("Request modifications to reduce risk exposure")
    alternatives.append("Compare with alternative lenders offering more favorable terms")
    return alternatives


def _build_final_result(risk_result: dict, llm_result: dict, clauses: list, source_text: str = None) -> dict:
    """Combine ML and LLM outputs into the final analysis payload."""
    llm_score = llm_result.get('overall_risk_score')
    ml_score = risk_result.get('score')

    is_fallback = llm_result.get('llm_fallback')

    if is_fallback:
        print("Warning: LLM returned fallback response, using ML score")
        score = ml_score if ml_score is not None else 5.0
    else:
        score = llm_score if llm_score is not None else ml_score
        score = 5.0 if score is None else float(score)

    rating, recommendation = _score_to_rating(score)

    # If LLM failed and no clauses, generate from ML
    if not clauses and is_fallback and source_text:
        clauses = _generate_ml_clauses(source_text)

    summary = llm_result.get('summary', '')
    if not summary:
        summary = _generate_fallback_summary(score, rating, recommendation, clauses)

    checklist = llm_result.get('checklist', [])
    if not checklist and is_fallback:
        checklist = _generate_fallback_checklist(clauses)

    questions = llm_result.get('questions_for_lender', [])
    if not questions and is_fallback:
        questions = _generate_fallback_questions(clauses)

    alternatives = llm_result.get('alternatives_if_refused', [])
    if not alternatives and is_fallback:
        alternatives = _generate_fallback_alternatives(clauses)

    return {
        'overall_risk_score': round(score, 1),
        'overall_rating': rating,
        'recommendation': recommendation,
        'summary': summary,
        'clauses': clauses,
        'checklist': checklist,
        'questions_for_lender': questions,
        'alternatives_if_refused': alternatives,
    }


def _generate_fallback_summary(score: float, rating: str, recommendation: str, clauses: list) -> str:
    """Generate a summary from available data when LLM summary is missing."""
    parts = [f"Overall risk score is {round(score, 1)} out of 10 - rated as {rating}."]
    if recommendation:
        parts.append(f"Recommendation: {recommendation}.")
    harmful = [c for c in clauses if c.get('category') == 'harmful']
    beneficial = [c for c in clauses if c.get('category') == 'beneficial']
    if harmful:
        parts.append(f"Found {len(harmful)} potentially harmful clause(s) that may need attention.")
    if beneficial:
        parts.append(f"Identified {len(beneficial)} beneficial clause(s) in your favor.")
    return " ".join(parts)


def _score_to_rating(score: float) -> tuple:
    if score <= 3:
        return 'Good', 'Safe to Sign'
    if score <= 6:
        return 'Mixed', 'Negotiate Terms'
    return 'Bad', 'Walk Away or Seek Alternatives'


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("")
async def analyze_document_endpoint(req: AnalyzeRequest, request: Request):
    """Analyze a document for clause risks."""
    db = await get_database()
    user = await get_required_user(request)

    document = await get_document(db, req.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get('user_id') != user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not req.force_reanalyze:
        existing = await get_document_analysis(db, req.document_id)
        if existing:
            return {'success': True, 'analysis': existing, 'cached': True}

    await update_document_status(db, req.document_id, 'processing')

    try:
        extracted_text = document['extracted_text']
        document_type = document['document_type']

        risk_result = _run_ml_risk_scoring(extracted_text)
        llm_result = await _run_llm_analysis(extracted_text, document_type)
        clauses = await _run_clause_analysis(extracted_text, document_type)
        clauses = _merge_ml_classifications(clauses)

        result = _build_final_result(risk_result, llm_result, clauses, source_text=extracted_text)

        analysis = await create_analysis(db, req.document_id, result)
        await update_document_status(db, req.document_id, 'analyzed', datetime.now(timezone.utc))

        return {'success': True, 'analysis': analysis, 'cached': False}

    except Exception as e:
        await update_document_status(db, req.document_id, 'error')
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{document_id}")
async def get_analysis(document_id: str, request: Request):
    """Get analysis for a document."""
    db = await get_database()
    user = await get_required_user(request)

    document = await get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get('user_id') != user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")

    analysis = await get_document_analysis(db, document_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found. Please run analysis first.")

    return {'success': True, 'document': document, 'analysis': analysis}


@router.get("/documents/list")
async def list_documents(request: Request):
    """List all documents for the current user."""
    user = await get_required_user(request)
    db = await get_database()

    documents = await get_user_documents(db, user['user_id'])

    for doc in documents:
        analysis = await get_document_analysis(db, doc['document_id'])
        doc['has_analysis'] = analysis is not None
        if analysis:
            doc['risk_score'] = analysis.get('overall_risk_score')
            doc['rating'] = analysis.get('overall_rating')

    return {'success': True, 'documents': documents}


@router.delete("/{document_id}")
async def delete_document_endpoint(document_id: str, request: Request):
    """Delete a document and its analysis."""
    db = await get_database()

    document = await get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    user = await get_required_user(request)
    if document.get('user_id') != user['user_id']:
        raise HTTPException(status_code=403, detail="Not authorized")

    delete_document_collection(document_id)
    await delete_document_analyses(db, document_id)
    await delete_document(db, document_id)

    return {'success': True, 'message': 'Document deleted'}
