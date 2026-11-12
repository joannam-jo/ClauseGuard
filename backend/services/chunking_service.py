"""Text chunking service with sentence awareness."""
import re
from typing import List, Optional

_nlp: Optional[object] = None


def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    import spacy
    try:
        _nlp = spacy.load("en_core_web_sm")
    except OSError:
        import subprocess
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_chunk_record(chunks: list, text: str) -> dict:
    """Build a chunk dict with the correct sequential index."""
    return {
        'text': text,
        'chunk_index': len(chunks),
        'char_count': len(text)
    }


def _flush_chunk(chunks: list, current_chunk: list, min_chunk_size: int) -> None:
    """Append *current_chunk* to *chunks*, merging into the previous entry if
    the combined text is below *min_chunk_size*."""
    chunk_text = " ".join(current_chunk)
    if len(chunk_text) >= min_chunk_size:
        chunks.append(_build_chunk_record(chunks, chunk_text))
    elif chunks:
        # Merge tiny chunk with the previous one
        chunks[-1]['text'] += " " + chunk_text
        chunks[-1]['char_count'] = len(chunks[-1]['text'])
    else:
        # First chunk is small but we still keep it
        chunks.append(_build_chunk_record(chunks, chunk_text))


def _build_overlap_window(sentences: list, overlap: int) -> list:
    """Return the suffix of *sentences* whose total length fits within *overlap*."""
    overlap_sentences: list = []
    overlap_length = 0
    for s in reversed(sentences):
        if overlap_length + len(s) <= overlap:
            overlap_sentences.insert(0, s)
            overlap_length += len(s)
        else:
            break
    return overlap_sentences


def _match_section_header(line: str, patterns: list) -> bool:
    """Return True if *line* matches any of the section header *patterns*."""
    for pattern in patterns:
        if re.match(pattern, line):
            return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    min_chunk_size: int = 300
) -> List[dict]:
    """Chunk text with sentence awareness and overlap.

    Returns:
        List of chunk dicts: {text, chunk_index, char_count}
    """
    doc = _get_nlp()(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    chunks: list = []
    current_chunk: list = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_length + sentence_len > chunk_size and current_chunk:
            _flush_chunk(chunks, current_chunk, min_chunk_size)

            # Carry forward an overlap window into the next chunk
            current_chunk = _build_overlap_window(current_chunk, overlap)
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_len

    # Flush whatever remains
    if current_chunk:
        _flush_chunk(chunks, current_chunk, min_chunk_size)

    return chunks


def extract_sections(text: str) -> List[dict]:
    """Extract named sections from document text."""
    section_patterns = [
        r'(?i)^\s*(?:SECTION|ARTICLE|CLAUSE)\s*([\d\.]+)[:\s]+(.+?)$',
        r'(?i)^\s*(\d+\.\d*)\s+(.+?)$',
        r'(?i)^\s*([A-Z][A-Z\s]+:)(.*)'
    ]

    sections = []
    current_section = None
    current_content: list = []

    for line in text.split('\n'):
        is_header = _match_section_header(line, section_patterns)
        if is_header:
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            current_section = line.strip()
            current_content = []
        elif line.strip():
            current_content.append(line)

    # Flush last section
    if current_section:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip()
        })

    return sections
