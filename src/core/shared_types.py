"""
core/types.py – Unified Article schema for news-mining.

Every crawler must return a dict that conforms to this schema (or an Article
dataclass instance, which can be converted to a dict with asdict()).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


@dataclass
class Article:
    # --- Identity ---
    url: str                           # canonical article URL
    source: str                        # 'vnexpress' | 'tuoitre'
    category: str                      # e.g. 'kinh-doanh', 'thoi-su'

    # --- Content ---
    title: str
    summary: Optional[str] = None
    content_text: str = ''             # cleaned plain-text body
    author: Optional[str] = None
    tags: Optional[list] = field(default_factory=list)

    # --- Time ---
    published_at: Optional[str] = None  # "YYYY-MM-DD HH:MM:SS" or None
    crawled_at: Optional[str] = None    # "YYYY-MM-DD HH:MM:SS"

    # --- Debug ---
    content_html_raw: Optional[str] = None  # raw HTML snippet (optional)

    # --- Derived (auto-computed if not provided) ---
    article_id: str = ''     # sha1(url)
    fingerprint: str = ''    # sha1(normalised content_text)

    def __post_init__(self):
        if not self.article_id and self.url:
            self.article_id = _sha1(self.url)
        if not self.fingerprint and self.content_text:
            # Normalise before hashing: collapse whitespace, lower-case
            import re
            normalized = re.sub(r'\s+', ' ', self.content_text).strip().lower()
            self.fingerprint = _sha1(normalized)

    def to_dict(self) -> dict:
        d = asdict(self)
        # Serialise tags list to comma-separated string for SQLite storage
        if isinstance(d.get('tags'), list):
            d['tags'] = ','.join(d['tags']) if d['tags'] else ''
        return d

    @staticmethod
    def required_fields() -> list:
        return ['url', 'source', 'category', 'title', 'crawled_at']
