# database/schema.py
import sqlite3
import sys
import os

# Use the canonical DB_PATH from config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.settings import DB_PATH


def init_db(db_path: str = DB_PATH):
    """Khởi tạo database với schema chuẩn cho Module 1."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id      TEXT UNIQUE NOT NULL,   -- sha1(url)
        url             TEXT UNIQUE NOT NULL,
        source          TEXT NOT NULL,           -- 'vnexpress' | 'tuoitre'
        category        TEXT,                    -- 'kinh-doanh', 'thoi-su', …
        title           TEXT NOT NULL,
        summary         TEXT,
        content_text    TEXT,                    -- cleaned plain-text body
        author          TEXT,
        tags            TEXT,                    -- comma-separated tag list
        published_at    TEXT,                    -- "YYYY-MM-DD HH:MM:SS" or NULL
        crawled_at      TEXT NOT NULL,           -- "YYYY-MM-DD HH:MM:SS"
        content_html_raw TEXT,                   -- raw HTML snippet (debug)
        fingerprint     TEXT,                    -- sha1(normalised content_text)
        created_at      TEXT DEFAULT (datetime('now'))
    )
    ''')

    # Index to speed up fingerprint-based dedup lookups
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_fingerprint ON articles(fingerprint)'
    )
    # Index for time-range queries using crawled_at (published_at may be NULL)
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_crawled_at ON articles(crawled_at)'
    )
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at)'
    )

    conn.commit()
    conn.close()
    print(f"✅ Database initialised at: {db_path}")


if __name__ == '__main__':
    init_db()