"""ML model endpoints."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

from api.deps import get_required_user
from ml.model_trainer import train_all_models, get_training_metrics, evaluate_models
from ml.clause_classifier import classify_clause, classify_clauses
from ml.risk_scorer import score_document_risk
from ml.document_classifier import classify_document_type

router = APIRouter(prefix="/ml", tags=["ml"])


class ClassifyRequest(BaseModel):
    text: str


class BatchClassifyRequest(BaseModel):
    texts: List[str]


@router.post("/train")
async def train_models(request: Request):
    """Train all ML models (requires authentication)."""
    await get_required_user(request)
    try:
        results = train_all_models()
        return {
            'success': True,
            'results': results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/metrics")
async def get_metrics(request: Request):
    """Get training metrics for all models (requires authentication)."""
    await get_required_user(request)
    metrics = get_training_metrics()
    evaluation = evaluate_models()
    
    return {
        'success': True,
        'training_metrics': metrics,
        'model_status': evaluation
    }


@router.post("/classify/clause")
async def classify_clause_endpoint(req: ClassifyRequest):
    """Classify a single clause as harmful or beneficial."""
    result = classify_clause(req.text)
    return {'success': True, 'result': result}


@router.post("/classify/clauses")
async def classify_clauses_endpoint(req: BatchClassifyRequest):
    """Classify multiple clauses."""
    results = classify_clauses(req.texts)
    return {'success': True, 'results': results}


@router.post("/risk-score")
async def risk_score_endpoint(req: ClassifyRequest):
    """Score document risk."""
    result = score_document_risk(req.text)
    return {'success': True, 'result': result}


@router.post("/classify/document-type")
async def classify_doc_type_endpoint(req: ClassifyRequest):
    """Classify document type."""
    result = classify_document_type(req.text)
    return {'success': True, 'result': result}
