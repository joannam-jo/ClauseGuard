"""PDF extraction service using PyMuPDF."""
import fitz  # PyMuPDF
from typing import Tuple, List
from pathlib import Path


def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """Extract text from a PDF file.
    
    Returns:
        Tuple of (extracted_text, page_count)
    """
    doc = fitz.open(file_path)
    text_parts = []
    page_count = doc.page_count
    
    for page_num in range(page_count):
        page = doc[page_num]
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
    
    doc.close()
    return "\n\n".join(text_parts), page_count


def extract_text_from_bytes(pdf_bytes: bytes) -> Tuple[str, int]:
    """Extract text from PDF bytes.
    
    Returns:
        Tuple of (extracted_text, page_count)
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    page_count = doc.page_count
    
    for page_num in range(page_count):
        page = doc[page_num]
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
    
    doc.close()
    return "\n\n".join(text_parts), page_count


def get_page_text(file_path: str, page_num: int) -> str:
    """Get text from a specific page."""
    doc = fitz.open(file_path)
    if page_num < 0 or page_num >= doc.page_count:
        doc.close()
        return ""
    
    page = doc[page_num]
    text = page.get_text()
    doc.close()
    return text


def search_in_pdf(file_path: str, query: str) -> List[dict]:
    """Search for text in PDF and return matching locations."""
    doc = fitz.open(file_path)
    results = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        instances = page.search_for(query)
        for inst in instances:
            results.append({
                'page': page_num + 1,
                'rect': {
                    'x0': inst.x0,
                    'y0': inst.y0,
                    'x1': inst.x1,
                    'y1': inst.y1
                }
            })
    
    doc.close()
    return results
