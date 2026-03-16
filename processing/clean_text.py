"""
processing/clean_text.py – Content cleaning utilities.

Removes noise from crawled Vietnamese news articles:
  - Script/style/nav/footer tags from raw HTML
  - Vietnamese boilerplate phrases ("Xem thêm", "Tin liên quan", etc.)
  - Advertisements and social prompts
  - Excessive whitespace
"""
from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Noise phrases – Vietnamese news boilerplate / ads / related-article blocks
# ---------------------------------------------------------------------------
_NOISE_PHRASES = [
    # Related article patterns
    r'bài liên quan[:\s]*',
    r'tin liên quan[:\s]*',
    r'xem thêm[:\s]*',
    r'đọc thêm[:\s]*',
    r'đọc tiếp[:\s]*',
    r'xem tiếp[:\s]*',
    r'có thể bạn quan tâm[:\s]*',
    r'tin cùng chuyên mục[:\s]*',
    r'video liên quan[:\s]*',
    # Social / sharing prompts
    r'chia sẻ bài viết[:\s]*',
    r'theo dõi[:\s]+\w+\s+trên',
    # Advertisement markers
    r'\[quảng cáo\]',
    r'\(quảng cáo\)',
    r'advertisement',
    # Common VNExpress / TuoiTre noise
    r'vnexpress\.net',
    r'tuoitre\.vn',
    # Comment / interaction prompts
    r'gửi bình luận',
    r'viết bình luận',
    r'đánh giá bài viết',
]

_NOISE_RE = re.compile(
    '|'.join(_NOISE_PHRASES),
    re.IGNORECASE | re.UNICODE,
)

# Tags whose entire subtree should be stripped from HTML before text extraction
_STRIP_TAGS = {
    'script', 'style', 'nav', 'footer', 'header', 'aside',
    'figure', 'figcaption', 'iframe', 'form', 'noscript',
    'ins',  # often used for Google ads
}

# CSS class / id fragments that indicate ad / related-article boxes
_AD_CLASS_PATTERNS = re.compile(
    r'(advert|advertisement|banner|promo|related|suggest|sidebar|widget|social|share)',
    re.IGNORECASE,
)

# Maximum content length (characters). Set to 0 to disable.
DEFAULT_MAX_LEN = 0  # unlimited by default; callers may override


def strip_html_noise(html: str) -> BeautifulSoup:
    """
    Parse raw HTML and remove noise elements (scripts, ads, nav, footer,
    related-article widgets, etc.).  Returns a BeautifulSoup object.
    """
    soup = BeautifulSoup(html, 'lxml')

    # 1. Remove by tag name
    for tag in _STRIP_TAGS:
        for elem in soup.find_all(tag):
            elem.decompose()

    # 2. Remove elements whose class or id looks like an ad / sidebar
    for elem in soup.find_all(True):
        classes = ' '.join(elem.get('class') or [])
        elem_id = elem.get('id') or ''
        if _AD_CLASS_PATTERNS.search(classes) or _AD_CLASS_PATTERNS.search(elem_id):
            elem.decompose()

    return soup


def clean_text(text: str, max_len: int = DEFAULT_MAX_LEN) -> str:
    """
    Clean plain text extracted from an article:
      1. Remove boilerplate / noise phrases
      2. Normalise whitespace (collapse multiple spaces / newlines)
      3. Optionally truncate to *max_len* characters (0 = no limit)
    """
    if not text:
        return ''

    # Remove noise phrases
    text = _NOISE_RE.sub(' ', text)

    # Normalise whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    if max_len and len(text) > max_len:
        # Truncate at word boundary to avoid splitting multi-byte chars or words
        truncated = text[:max_len]
        last_space = truncated.rfind(' ')
        if last_space > max_len // 2:
            truncated = truncated[:last_space]
        text = truncated

    return text


def extract_text_from_html(
    html: str,
    content_selector: Optional[str] = None,
    max_len: int = DEFAULT_MAX_LEN,
) -> str:
    """
    High-level helper: strip noise from raw HTML, extract all paragraph text,
    clean it, and return a plain-text string.

    Args:
        html: Raw HTML string.
        content_selector: Optional CSS selector to narrow extraction scope
            (e.g. ``"article.fck_detail"`` for VNExpress).  If not provided
            or not found, falls back to the whole cleaned document.
        max_len: Maximum number of characters to return (0 = no limit).
    """
    soup = strip_html_noise(html)

    # Narrow scope if selector provided
    root = soup
    if content_selector:
        found = soup.select_one(content_selector)
        if found:
            root = found

    # Collect paragraph text (and fall back to all text if <p> is empty)
    paragraphs = root.find_all('p')
    if paragraphs:
        parts = [p.get_text(separator=' ') for p in paragraphs]
    else:
        parts = [root.get_text(separator='\n')]

    raw_text = '\n'.join(parts)
    return clean_text(raw_text, max_len=max_len)
