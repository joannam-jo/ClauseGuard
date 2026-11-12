"""
Finance Agreement Analyzer - FastAPI Backend
RAG-based document analysis with ML-powered clause classification
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Set model cache directory before any ML imports
BACKEND_DIR = Path(__file__).resolve().parent
MODEL_CACHE_DIR = str(BACKEND_DIR / 'model_cache')
os.environ['HF_HOME'] = MODEL_CACHE_DIR
os.environ['TRANSFORMERS_CACHE'] = MODEL_CACHE_DIR

from core.config import CORS_ORIGINS, ML_MODELS_DIR, UPLOAD_DIR, CHROMA_PERSIST_DIR
from core.limiter import limiter
from api.endpoints import auth, upload, analyze, chat, ml


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("=" * 50)
    print("Finance Agreement Analyzer - Starting...")
    print("=" * 50)
    
    # Ensure directories exist
    Path(ML_MODELS_DIR).mkdir(exist_ok=True)
    Path(UPLOAD_DIR).mkdir(exist_ok=True)
    Path(CHROMA_PERSIST_DIR).mkdir(exist_ok=True)
    
    # Pre-load ML models
    print("Loading ML models...")
    try:
        from ml.clause_classifier import get_clause_classifier
        from ml.risk_scorer import get_risk_scorer
        from ml.document_classifier import get_doc_type_classifier
        
        get_clause_classifier()
        get_risk_scorer()
        get_doc_type_classifier()
        print("ML models loaded successfully!")
    except Exception as e:
        print(f"Warning: Could not load ML models: {e}")
    
    # Pre-load embedding model
    print("Loading embedding model...")
    try:
        from services.embedding_service import get_model
        get_model()
        print("Embedding model loaded successfully!")
    except Exception as e:
        print(f"Warning: Could not load embedding model: {e}")
    
    print("=" * 50)
    print("Server ready!")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Finance Agreement Analyzer API",
    description="RAG-based finance agreement analysis with ML-powered clause classification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
origins = CORS_ORIGINS.split(",") if "," in CORS_ORIGINS else [CORS_ORIGINS]
if CORS_ORIGINS == "*":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ml.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Finance Agreement Analyzer API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Finance Agreement Analyzer",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
