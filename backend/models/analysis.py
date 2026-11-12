"""Analysis model and database operations."""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.security import generate_analysis_id


class ClauseAnalysis(BaseModel):
    clause_id: str
    title: str
    text: str
    risk_level: str  # HIGH, MEDIUM, LOW, BENEFICIAL
    category: str  # harmful or beneficial
    explanation: str
    negotiation_suggestion: Optional[str] = None
    confidence: float  # 0-1
    page_number: Optional[int] = None
    section: Optional[str] = None


class AnalysisResult(BaseModel):
    analysis_id: str
    document_id: str
    overall_risk_score: float  # 0-10
    overall_rating: str  # Good, Mixed, Bad
    recommendation: str  # Sign, Negotiate, Walk Away
    summary: str
    clauses: List[ClauseAnalysis]
    checklist: List[str]
    questions_for_lender: List[str]
    alternatives_if_refused: List[str]
    created_at: datetime


def serialize_analysis(analysis: dict) -> dict:
    """Serialize analysis for API response."""
    if '_id' in analysis:
        del analysis['_id']
    if isinstance(analysis.get('created_at'), datetime):
        analysis['created_at'] = analysis['created_at'].isoformat()
    return analysis


async def create_analysis(db: AsyncIOMotorDatabase, document_id: str, result: dict) -> dict:
    """Save analysis result to database."""
    analysis_id = generate_analysis_id()
    analysis = {
        'analysis_id': analysis_id,
        'document_id': document_id,
        'overall_risk_score': result.get('overall_risk_score', 5.0),
        'overall_rating': result.get('overall_rating', 'Mixed'),
        'recommendation': result.get('recommendation', 'Review Carefully'),
        'summary': result.get('summary', ''),
        'clauses': result.get('clauses', []),
        'checklist': result.get('checklist', []),
        'questions_for_lender': result.get('questions_for_lender', []),
        'alternatives_if_refused': result.get('alternatives_if_refused', []),
        'created_at': datetime.now(timezone.utc)
    }
    
    await db.analyses.insert_one(analysis)
    return serialize_analysis(analysis.copy())


async def get_analysis(db: AsyncIOMotorDatabase, analysis_id: str) -> Optional[dict]:
    """Get analysis by ID."""
    analysis = await db.analyses.find_one({'analysis_id': analysis_id}, {'_id': 0})
    if analysis:
        return serialize_analysis(analysis.copy())
    return None


async def get_document_analysis(db: AsyncIOMotorDatabase, document_id: str) -> Optional[dict]:
    """Get the latest analysis for a document."""
    analysis = await db.analyses.find_one(
        {'document_id': document_id},
        {'_id': 0},
        sort=[('created_at', -1)]
    )
    if analysis:
        return serialize_analysis(analysis.copy())
    return None


async def delete_document_analyses(db: AsyncIOMotorDatabase, document_id: str):
    """Delete all analyses for a document."""
    await db.analyses.delete_many({'document_id': document_id})
