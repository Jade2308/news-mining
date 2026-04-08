# database/schema.py
import sqlite3
import sys
import os

# Use the canonical DB_PATH from config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


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

    cursor.execute("PRAGMA table_info(articles)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    prediction_columns = {
        'predicted_label': 'TEXT',
        'prediction_score': 'REAL',
        'model_version': 'TEXT',
        'labeled_at': 'TEXT',
    }

    for column_name, column_type in prediction_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f'ALTER TABLE articles ADD COLUMN {column_name} {column_type}')

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
    # Index để query dự đoán nhanh
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_predicted_label ON articles(predicted_label)'
    )
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_labeled_at ON articles(labeled_at)')

    # --- BẢNG LƯU CHỦ ĐỀ HOT ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hot_topics (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_name      TEXT NOT NULL,
        keywords        TEXT NOT NULL,
        article_count   INTEGER DEFAULT 0,
        timeframe       INTEGER,
        created_at      TEXT DEFAULT (datetime('now'))
    )
    ''')
    
    cursor.execute("PRAGMA table_info(hot_topics)")
    hot_topics_existing_columns = {row[1] for row in cursor.fetchall()}
    if 'timeframe' not in hot_topics_existing_columns:
        cursor.execute('ALTER TABLE hot_topics ADD COLUMN timeframe INTEGER')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topic_articles (
        topic_id        INTEGER NOT NULL,
        article_id      TEXT NOT NULL,
        FOREIGN KEY(topic_id) REFERENCES hot_topics(id),
        FOREIGN KEY(article_id) REFERENCES articles(article_id),
        UNIQUE(topic_id, article_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialised at: {db_path}")


if __name__ == '__main__':
    init_db()