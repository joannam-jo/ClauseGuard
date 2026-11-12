"""LLM service using the local OpenAI client wrapper."""
import json
import re
import uuid
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from integrations.llm.chat import LlmChat, UserMessage
from core.config import (
    LLM_API_KEY,
    LLM_PROVIDER,
    LLM_MODEL,
    OLLAMA_MAX_ANALYSIS_CHARS,
    OLLAMA_MAX_CLAUSE_CHARS,
    OLLAMA_MAX_CHAT_CHARS,
)
from prompts.analysis_prompt import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt
from prompts.clause_risk_prompt import CLAUSE_ANALYSIS_SYSTEM_PROMPT, build_clause_prompt
from prompts.negotiation_prompt import CHAT_SYSTEM_PROMPT, build_chat_prompt


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------

async def analyze_document(document_text: str, document_type: str, context_chunks: list = None) -> dict:
    """Analyze a finance document and return structured results."""
    _require_llm_key()
    chat = _build_chat(f"analysis_{hash(document_text[:100])}", ANALYSIS_SYSTEM_PROMPT)
    source_text = _limit_for_ollama(document_text, OLLAMA_MAX_ANALYSIS_CHARS)
    prompt = build_analysis_prompt(source_text, document_type)
    response = await chat.send_message(UserMessage(text=prompt))
    return parse_analysis_response(response, document_type)


async def analyze_clauses_detailed(clauses_text: str, document_type: str) -> list:
    """Analyze individual clauses in detail."""
    _require_llm_key()
    chat = _build_chat(f"clause_analysis_{hash(clauses_text[:100])}", CLAUSE_ANALYSIS_SYSTEM_PROMPT)
    source_text = _limit_for_ollama(clauses_text, OLLAMA_MAX_CLAUSE_CHARS)
    prompt = build_clause_prompt(source_text, document_type)
    response = await chat.send_message(UserMessage(text=prompt))
    return parse_clause_response(response)


async def chat_with_document(document_id: str, query: str, context: str, chat_history: list = None) -> str:
    """Chat with a document using RAG context."""
    _require_llm_key()
    chat = _build_chat(f"chat_{document_id}", CHAT_SYSTEM_PROMPT)
    trimmed_context = _limit_for_ollama(context, OLLAMA_MAX_CHAT_CHARS)
    prompt = build_chat_prompt(query, trimmed_context, chat_history)
    return await chat.send_message(UserMessage(text=prompt))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _require_llm_key() -> None:
    if LLM_PROVIDER != "ollama" and not LLM_API_KEY:
        raise ValueError("LLM_API_KEY not configured")


def _limit_for_ollama(text: str, max_chars: int) -> str:
    if LLM_PROVIDER != "ollama":
        return text
    if not text:
        return text
    return text[:max_chars]


def _build_chat(session_id: str, system_message: str) -> LlmChat:
    return (
        LlmChat(
            api_key=LLM_API_KEY,
            session_id=session_id,
            system_message=system_message,
        )
        .with_model(LLM_PROVIDER, LLM_MODEL)
    )


# ---------------------------------------------------------------------------
# Analysis response parser
# ---------------------------------------------------------------------------

def parse_analysis_response(response: str, document_type: str) -> dict:
    """Parse LLM analysis response into structured format."""
    parsed = _extract_json_payload(response)
    if isinstance(parsed, dict):
        score = _coerce_score(parsed.get('overall_risk_score'))
        rating = _normalize_rating(parsed.get('overall_rating'))
        recommendation = _normalize_recommendation(parsed.get('recommendation'))

        if not rating and score is not None:
            rating, recommendation = _score_to_rating(score)
        if not recommendation and score is not None:
            _, recommendation = _score_to_rating(score)

        return {
            'overall_risk_score': score,
            'overall_rating': rating,
            'recommendation': recommendation,
            'summary': (parsed.get('summary') or '').strip()[:500],
            'clauses': [],
            'checklist': _normalize_list(parsed.get('checklist')),
            'questions_for_lender': _normalize_list(parsed.get('questions_for_lender')),
            'alternatives_if_refused': _normalize_list(parsed.get('alternatives_if_refused')),
            'raw_response': response,
        }

    if _is_fallback_response(response):
        return {
            'overall_risk_score': None,
            'overall_rating': None,
            'recommendation': None,
            'summary': '',
            'clauses': [],
            'checklist': [],
            'questions_for_lender': [],
            'alternatives_if_refused': [],
            'raw_response': response,
            'llm_fallback': True,
        }

    score = _extract_risk_score(response)
    rating, recommendation = _score_to_rating(score) if score is not None else (None, None)

    return {
        'overall_risk_score': score,
        'overall_rating': rating,
        'recommendation': recommendation,
        'summary': _extract_summary(response),
        'clauses': [],
        'checklist': _extract_bullet_section(response, r'(?:checklist|before signing)'),
        'questions_for_lender': _extract_bullet_section(response, r'(?:questions|ask the lender)'),
        'alternatives_if_refused': _extract_bullet_section(response, r'(?:alternatives|if they refuse)'),
        'raw_response': response,
    }


def _is_fallback_response(response: str) -> bool:
    """Detect mock/fallback LLM responses that hardcode scores."""
    if not response:
        return True
    stripped = response.strip()
    if stripped.startswith('# Clause Analysis') or stripped.startswith('# Analysis Report'):
        return True
    if '## Executive Summary' in stripped and ('## Risk Score: 8.5' in stripped or '## Risk Score: 4.5' in stripped):
        return True
    return False


def _extract_risk_score(response: str) -> Optional[float]:
    match = re.search(
        r'(?:risk\s*score|overall\s*score)\s*[:\-\s]*([0-9]+(?:\.[0-9]+)?)',
        response.lower()
    )
    if match:
        return _coerce_score(match.group(1))
    return None


def _score_to_rating(score: float):
    if score <= 3:
        return 'Good', 'Safe to Sign'
    if score <= 6:
        return 'Mixed', 'Negotiate Terms'
    return 'Bad', 'Walk Away or Seek Alternatives'


def _extract_summary(response: str) -> str:
    match = re.search(
        r'(?:summary|overview|executive summary)[:\s]*([^#]+?)(?=\n#|\n\n\*\*|$)',
        response,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()[:500]
    return response[:500].strip()


def _extract_bullet_section(response: str, section_pattern: str) -> list:
    match = re.search(
        rf'(?:{section_pattern})[:\s]*([^#]+?)(?=\n#|$)',
        response,
        re.IGNORECASE,
    )
    if not match:
        return []
    items = re.findall(r'[-•\*\d\.\)]\s*(.+?)(?=\n|$)', match.group(1))
    return [i.strip() for i in items[:10]]


# ---------------------------------------------------------------------------
# Clause response parser
# ---------------------------------------------------------------------------

def parse_clause_response(response: str) -> list:
    """Parse clause analysis response into list of clause objects."""
    if _is_fallback_response(response):
        return []

    parsed = _extract_json_payload(response)
    if isinstance(parsed, list):
        clauses = []
        for entry in parsed:
            normalized = _normalize_clause_entry(entry)
            if normalized:
                clauses.append(normalized)
        if clauses:
            return clauses

    clauses = []
    sections = re.split(
        r'(?=###\s*|##\s+|(?<=\n)\*\*[^\*]+\*\*|(?<=\n)\d+\.\s+[A-Z])',
        response,
    )

    for section in sections:
        if not section.strip() or len(section.strip()) < 30:
            continue
        clause = _build_clause_from_section(section)
        if clause['text'] and len(clause['text']) > 20:
            clauses.append(clause)

    return clauses


def _build_clause_from_section(section: str) -> dict:
    """Extract all fields from a single clause section block."""
    risk_level, category = _extract_risk_and_category(section)
    return {
        'clause_id': f"clause_{uuid.uuid4().hex[:8]}",
        'title': _extract_title(section),
        'text': _extract_clause_text(section),
        'risk_level': risk_level,
        'category': category,
        'explanation': _extract_field(section, r'(?:why|explanation|reason|analysis)'),
        'negotiation_suggestion': _extract_field(section, r'(?:negotiat|suggest|request|recommendation)') or None,
        'confidence': _extract_confidence(section),
        'page_number': _extract_page_number(section),
        'section': _extract_field(section, r'(?:section|article|clause)\s*[\d\.]+') or None,
    }


def _extract_title(section: str) -> str:
    match = re.search(r'^(?:###\s*)?(?:\*\*)?([^\*\n:]+)(?:\*\*)?', section)
    return match.group(1).strip()[:100] if match else 'Clause'


def _extract_risk_and_category(section: str) -> tuple:
    lower = section.lower()
    if re.search(r'\b(high|critical|severe)\b', lower):
        return 'HIGH', 'harmful'
    if re.search(r'\b(low|minimal|safe|good)\b', lower):
        return 'LOW', 'beneficial'
    if re.search(r'\b(beneficial|favorable|positive)\b', lower):
        return 'BENEFICIAL', 'beneficial'
    return 'MEDIUM', 'neutral'


def _extract_clause_text(section: str) -> str:
    match = re.search(
        r'(?:text|content|clause text)[:\s]*([^\n]+(?:\n(?![*#\-]).*)*)',
        section,
        re.IGNORECASE,
    )
    if match:
        text = match.group(1).strip()[:500]
        # Strip leading non-word chars (colons, quotes) and trailing quotes
        text = text.lstrip(':;,\'"').strip()
        text = text.rstrip('"\'')
    else:
        text = section.strip()[:500]
    # Final cleanup: if text is wrapped in quotes, remove them
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    return text.strip()[:500]


def _extract_field(section: str, pattern: str) -> str:
    match = re.search(
        rf'(?:{pattern})[:\s]*([^\n]+(?:\n(?![*#\-])[^\n]*)*)',
        section,
        re.IGNORECASE,
    )
    return match.group(1).strip()[:300] if match else ''


def _extract_confidence(section: str) -> float:
    match = re.search(r'confidence[:\s]*(\d+)%?', section, re.IGNORECASE)
    if match:
        return _normalize_confidence(match.group(1))
    return 0.7


def _extract_json_payload(response: str):
    cleaned = _strip_code_fences(response)

    # Prefer JSON arrays if present
    array_start = cleaned.find('[')
    obj_start = cleaned.find('{')
    if array_start != -1 and (obj_start == -1 or array_start < obj_start):
        array_end = cleaned.rfind(']')
        if array_end != -1 and array_end > array_start:
            payload = cleaned[array_start:array_end + 1]
            try:
                return json.loads(payload)
            except Exception:
                pass

    if obj_start != -1:
        obj_end = cleaned.rfind('}')
        if obj_end != -1 and obj_end > obj_start:
            payload = cleaned[obj_start:obj_end + 1]
            try:
                return json.loads(payload)
            except Exception:
                pass

    try:
        return json.loads(cleaned)
    except Exception:
        return None


def _strip_code_fences(text: str) -> str:
    fence_match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text, re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()
    return text.strip()


def _normalize_list(value) -> list:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()][:10]
    if isinstance(value, str):
        items = re.findall(r'[-•\*\d\.\)]\s*(.+?)(?=\n|$)', value)
        if items:
            return [i.strip() for i in items[:10]]
        value = value.strip()
        return [value] if value else []
    return []


def _normalize_confidence(value) -> float:
    try:
        val = float(value)
    except Exception:
        return 0.7
    if val > 1.0:
        val = val / 100.0
    return min(1.0, max(0.0, val))


def _coerce_score(value) -> Optional[float]:
    try:
        score = float(value)
    except Exception:
        match = re.search(r'([0-9]+(?:\.[0-9]+)?)', str(value))
        if not match:
            return None
        score = float(match.group(1))
    return min(10.0, max(0.0, score))


def _normalize_rating(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip().title()
    if normalized in {'Good', 'Mixed', 'Bad'}:
        return normalized
    return None


def _normalize_recommendation(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = str(value).strip()
    allowed = {
        'Safe to Sign',
        'Negotiate Terms',
        'Walk Away',
        'Walk Away or Seek Alternatives',
    }
    return normalized if normalized in allowed else None


def _normalize_clause_entry(entry) -> Optional[dict]:
    if not isinstance(entry, dict):
        return None

    text = str(entry.get('text') or '').strip()
    if not text:
        return None

    risk_level = str(entry.get('risk_level') or '').strip().upper()
    if risk_level not in {'HIGH', 'MEDIUM', 'LOW', 'BENEFICIAL'}:
        risk_level = 'MEDIUM'

    category = str(entry.get('category') or '').strip().lower()
    if category not in {'harmful', 'beneficial', 'neutral'}:
        category = 'neutral'

    return {
        'clause_id': f"clause_{uuid.uuid4().hex[:8]}",
        'title': str(entry.get('title') or 'Clause').strip()[:100],
        'text': text[:500],
        'risk_level': risk_level,
        'category': category,
        'explanation': str(entry.get('explanation') or '').strip()[:300],
        'negotiation_suggestion': (str(entry.get('negotiation_suggestion')).strip()[:300]
                                   if entry.get('negotiation_suggestion') else None),
        'confidence': _normalize_confidence(entry.get('confidence')),
        'page_number': _coerce_page_number(entry.get('page_number')),
        'section': str(entry.get('section') or '').strip()[:100] or None,
    }


def _coerce_page_number(value) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _extract_page_number(section: str) -> Optional[int]:
    match = re.search(r'page\s*(?:no|#|number)?[:\s]*(\d+)', section, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None
