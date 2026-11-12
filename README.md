# Finance Agreement Analyzer

A production-grade RAG-based web application for analyzing finance agreements using machine learning. This academic ML project extracts, classifies, and evaluates clauses from loan agreements, lease contracts, and credit card terms.

## Features

### Core Features
- **PDF Upload & Extraction**: Upload finance agreement PDFs with automatic text extraction using PyMuPDF
- **Auto Document Type Detection**: ML-powered classification of document types (loan, lease, credit card)
- **Clause Risk Analysis**: Identifies harmful vs beneficial clauses with risk scoring
- **Side-by-Side View**: PDF viewer on the left, analysis results on the right
- **RAG-based Chat**: Ask questions about your document with context-aware AI responses
- **Risk Score Gauge**: Visual representation of overall document risk (0-10 scale)
- **Sortable Clause Table**: Summary table with filtering and sorting by risk level

### ML Components
- **Clause Classifier**: TF-IDF + Naive Bayes for harmful/beneficial classification
- **Risk Scorer**: TF-IDF + Random Forest for document risk prediction (0-10)
- **Document Type Classifier**: TF-IDF + SVM for loan/lease/credit card detection
- **Embedding Model**: all-MiniLM-L6-v2 (384-dim) for semantic search

### Additional Features
- **Dark/Light Mode**: Toggle between themes
- **Responsive Design**: Works on desktop, tablet, and mobile
- **User Authentication**: Email/password + Google OAuth
- **ML Dashboard**: View model metrics and retrain models

## Tech Stack

### Frontend
- React 18 with React Router
- Tailwind CSS + shadcn/ui components
- Zustand for state management
- react-pdf for PDF viewing
- Recharts for visualizations
- react-dropzone for file upload
- react-markdown for rendering

### Backend
- FastAPI with async support
- MongoDB with Motor async driver
- PyMuPDF for PDF extraction
- sentence-transformers for embeddings
- ChromaDB for vector storage
- scikit-learn for ML models
- SpaCy for NLP
- LLM provider: OpenAI or Ollama

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB 6.0+

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download SpaCy model
python -m spacy download en_core_web_sm

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Start the server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
yarn install

# Create .env file
cp .env.example .env
# Edit .env with your backend URL

# Start development server
yarn start
```

### Environment Variables

#### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=finance_analyzer
CORS_ORIGINS=http://localhost:3000
LLM_API_KEY=your-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=180
OLLAMA_NUM_PREDICT=512
OLLAMA_MAX_ANALYSIS_CHARS=6000
OLLAMA_MAX_CLAUSE_CHARS=8000
OLLAMA_MAX_CHAT_CHARS=4000
CHROMA_PERSIST_DIR=/path/to/chroma_db
JWT_SECRET=your-secret-key
OAUTH_SESSION_URL=your-oauth-session-endpoint  # Optional: enable Google OAuth
```

#### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_GOOGLE_OAUTH_URL=your-google-oauth-url  # Optional: enable Google OAuth

## Ollama (Local LLM)

1) Install Ollama: https://ollama.com
2) Pull a model (example):
```bash
ollama pull llama3
```
3) Set backend env vars:
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=180
OLLAMA_NUM_PREDICT=512
OLLAMA_MAX_ANALYSIS_CHARS=6000
OLLAMA_MAX_CLAUSE_CHARS=8000
OLLAMA_MAX_CHAT_CHARS=4000
```
```

## Usage

1. **Upload a Document**: Go to `/upload` and drag-drop your PDF
2. **Wait for Analysis**: The system extracts text, classifies clauses, and generates risk assessment
3. **Review Results**: View the side-by-side analysis with PDF on left, results on right
4. **Ask Questions**: Use the chat interface to ask about specific clauses
5. **Export**: Download the analysis as a PDF report

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/session` - Process Google OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Documents
- `POST /api/upload` - Upload PDF document
- `GET /api/upload/{document_id}/file` - Get original PDF
- `GET /api/analyze/documents/list` - List user's documents
- `DELETE /api/analyze/{document_id}` - Delete document

### Analysis
- `POST /api/analyze` - Trigger analysis for a document
- `GET /api/analyze/{document_id}` - Get analysis results

### Chat
- `POST /api/chat` - Send chat message with document context
- `POST /api/chat/search` - Semantic search in document

### ML Models
- `POST /api/ml/train` - Train all models
- `GET /api/ml/metrics` - Get model metrics
- `POST /api/ml/classify/clause` - Classify single clause
- `POST /api/ml/risk-score` - Score document risk
- `POST /api/ml/classify/document-type` - Classify document type

## ML Pipeline

```
PDF Upload
    ↓
PyMuPDF Text Extraction (multi-page)
    ↓
Document Type Auto-Detection (SVM)
    ↓
Sentence-Aware Chunking (1000 chars, 200 overlap)
    ↓
all-MiniLM-L6-v2 Embeddings (384-dim)
    ↓
ChromaDB Persistent Storage
    ↓
RAG Retrieval (top-5 similar chunks)
    ↓
OpenAI GPT-4 Analysis
    ↓
Risk Score + Clause Classification
```

## Harmful Clauses Detected

- Penalty rates > 3% per month
- Unilateral modification rights
- Auto-renewal without notice
- Hidden or unclear fees
- Biased arbitration clauses
- Acceleration without grace period
- Cross-collateralization
- Waived consumer rights
- Inconvenient jurisdiction
- Confession of judgment

## Beneficial Clauses Highlighted

- Fair interest rates (below market)
- Grace periods for payments
- No prepayment penalty
- Transparent fee schedules
- Right to cure defaults
- Rate caps or guarantees
- Consumer protections
- Fair dispute resolution

## Project Structure

```
/app
├── backend/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── upload.py
│   │   │   ├── analyze.py
│   │   │   ├── chat.py
│   │   │   └── ml.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── user.py
│   │   ├── document.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── pdf_service.py
│   │   ├── chunking_service.py
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   ├── rag_service.py
│   │   └── llm_service.py
│   ├── ml/
│   │   ├── clause_classifier.py
│   │   ├── risk_scorer.py
│   │   ├── document_classifier.py
│   │   └── model_trainer.py
│   ├── prompts/
│   │   ├── analysis_prompt.py
│   │   ├── clause_risk_prompt.py
│   │   └── negotiation_prompt.py
│   ├── server.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload.jsx
│   │   │   ├── PDFViewer.jsx
│   │   │   ├── AnalysisDashboard.jsx
│   │   │   ├── ClauseRiskCard.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── RiskScoreGauge.jsx
│   │   │   └── ClauseSummaryTable.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── UploadPage.jsx
│   │   │   ├── AnalysisPage.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── MLDashboard.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   └── RegisterPage.jsx
│   │   ├── hooks/
│   │   ├── store/
│   │   ├── services/
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
└── README.md
```

## License

This project is for academic purposes only. See LICENSE for details.

## Disclaimer

This tool uses machine learning models for educational purposes. Model outputs are probabilistic and may be incomplete. Always consult a legal professional for important financial decisions.
