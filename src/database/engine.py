# database/db.py
import sqlite3
import sys
import os
from datetime import datetime, timezone, timedelta

# Use the canonical DB_PATH from config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.settings import DB_PATH

_VN_TZ = timezone(timedelta(hours=7))


def get_connection(db_path: str = DB_PATH):
    """Return a SQLite connection."""
    return sqlite3.connect(db_path)


def insert_article(data: dict, db_path: str = DB_PATH) -> str:
    """
    Insert an article into the DB.

    Returns:
        'inserted'   – new row was created
        'dup_url'    – URL already exists
        'dup_fp'     – different URL but same fingerprint (content duplicate)
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        # URL-based dedup first
        cursor.execute('SELECT id FROM articles WHERE url = ?', (data['url'],))
        if cursor.fetchone():
            return 'dup_url'

        # Fingerprint-based dedup (content duplicate, possibly different URL)
        fp = data.get('fingerprint')
        if fp:
            cursor.execute(
                'SELECT id FROM articles WHERE fingerprint = ?', (fp,)
            )
            if cursor.fetchone():
                return 'dup_fp'

        # crawled_at is always set by the crawler at crawl time; fallback is a
        # safety net in case insert is called with incomplete data.
        crawled_at = data.get('crawled_at') or datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
        INSERT INTO articles (
            article_id, url, source, category,
            title, summary, content_text, author, tags,
            published_at, crawled_at, content_html_raw, fingerprint
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('article_id'),
            data['url'],
            data['source'],
            data.get('category'),
            data['title'],
            data.get('summary'),
            data.get('content_text'),
            data.get('author'),
            data.get('tags'),
            data.get('published_at'),
            crawled_at,
            data.get('content_html_raw'),
            fp,
        ))
        conn.commit()
        return 'inserted'
    except sqlite3.IntegrityError:
        return 'dup_url'
    finally:
        conn.close()


def get_all_articles(limit: int = 1000, db_path: str = DB_PATH) -> list:
    """Return up to *limit* articles as a list of dicts."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM articles LIMIT ?', [limit])
    columns = [d[0] for d in cursor.description]
    articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return articles


def get_articles_by_timerange(hours: int = 24, limit: int = 1000, db_path: str = DB_PATH) -> list:
    """Return articles crawled within the last *hours* hours."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM articles
    WHERE crawled_at > datetime('now', '-' || ? || ' hours')
    ORDER BY crawled_at DESC
    LIMIT ?
    ''', [hours, limit])
    columns = [d[0] for d in cursor.description]
    articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return articles


def count_articles(db_path: str = DB_PATH) -> int:
    """Return total number of articles in the DB."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM articles')
    count = cursor.fetchone()[0]
    conn.close()
    return count


if __name__ == '__main__':
    print(f"Total articles: {count_articles()}")