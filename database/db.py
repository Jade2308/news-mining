# database/db.py
import sqlite3
import sys
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

# Use the canonical DB_PATH from config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

_VN_TZ = timezone(timedelta(hours=7))
logger = logging.getLogger(__name__)

_CLICKBAIT_MODEL = None
_CLICKBAIT_MODEL_DISABLED = False


def _get_clickbait_model():
    """Lazy-load PhoBERT model for clickbait detection.

    Returns None if model is unavailable. This must never break crawling.
    """
    global _CLICKBAIT_MODEL, _CLICKBAIT_MODEL_DISABLED

    if _CLICKBAIT_MODEL_DISABLED:
        return None
    if _CLICKBAIT_MODEL is not None:
        return _CLICKBAIT_MODEL

    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'phobert_clickbait')
    if not os.path.isdir(model_dir):
        _CLICKBAIT_MODEL_DISABLED = True
        logger.info("PhoBERT model not found at models/phobert_clickbait. Skip clickbait detection.")
        return None

    try:
        from src.models.phobert_classifier import PhoBERTClickbaitClassifier
        _CLICKBAIT_MODEL = PhoBERTClickbaitClassifier(model_name=model_dir)
        logger.info("PhoBERT clickbait model loaded successfully.")
    except Exception as exc:
        _CLICKBAIT_MODEL_DISABLED = True
        logger.warning(f"Cannot load PhoBERT model, skip clickbait detection: {exc}")
        return None

    return _CLICKBAIT_MODEL


def predict_clickbait(data: dict) -> Tuple[int, float, str]:
    """Predict clickbait from article title/summary.

    Returns:
        (label, confidence, label_name)
    """
    model = _get_clickbait_model()
    if model is None:
        return 0, 0.5, 'non-clickbait'

    title = (data.get('title') or '').strip()
    summary = (data.get('summary') or '').strip()
    text = f"{title} {summary}".strip() if summary else title
    if not text:
        return 0, 0.5, 'non-clickbait'

    try:
        label, confidence = model.predict(text)
        return label, confidence, ('clickbait' if label == 1 else 'non-clickbait')
    except Exception as exc:
        logger.warning(f"Clickbait prediction failed: {exc}")
        return 0, 0.5, 'non-clickbait'


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
        # Optional clickbait detection (no DB schema changes required)
        label, confidence, label_name = predict_clickbait(data)
        data['clickbait_label'] = label
        data['clickbait_confidence'] = confidence

        if label == 1:
            logger.info(
                "Clickbait detected | confidence=%.2f | title=%s",
                confidence,
                (data.get('title') or '')[:120]
            )

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


def get_articles_by_timerange(hours: int = 24, db_path: str = DB_PATH) -> list:
    """Return articles crawled within the last *hours* hours."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM articles
    WHERE crawled_at > datetime('now', '-' || ? || ' hours')
    ORDER BY crawled_at DESC
    ''', [hours])
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


def save_hot_topics(topics_data: list, timeframe_hours: Optional[int] = None, db_path: str = DB_PATH):
    """
    Lưu các chủ đề hot vừa phát hiện vào DB.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')
    try:
        for t in topics_data:
            cursor.execute('''
                INSERT INTO hot_topics (topic_name, keywords, article_count, timeframe, created_at) 
                VALUES (?, ?, ?, ?, ?)
            ''', (t['topic_name'], t['keywords'], t['article_count'], timeframe_hours, now_str))
            
            topic_internal_id = cursor.lastrowid
            
            for a_id in t['article_ids']:
                try:
                    cursor.execute('''
                        INSERT INTO topic_articles (topic_id, article_id)
                        VALUES (?, ?)
                    ''', (topic_internal_id, a_id))
                except sqlite3.IntegrityError:
                    pass
        
        conn.commit()
        logger.info(f"✅ Successfully saved {len(topics_data)} hot topics to Database.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save hot topics: {e}")
    finally:
        conn.close()


def get_latest_hot_topics(timeframe_hours: int, db_path: str = DB_PATH) -> list:
    """
    Lấy danh sách các chủ đề hot nhất của lần chạy gần nhất cho một mốc thời gian.
    Dùng cho Dashboard.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT MAX(created_at) FROM hot_topics WHERE timeframe = ?
    ''', (timeframe_hours,))
    latest_time = cursor.fetchone()[0]
    
    if not latest_time:
        conn.close()
        return []
        
    cursor.execute('''
        SELECT id, topic_name, keywords, article_count, timeframe, created_at
        FROM hot_topics 
        WHERE timeframe = ? AND created_at = ?
    ''', (timeframe_hours, latest_time))
    
    columns = [d[0] for d in cursor.description]
    topics = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return topics


if __name__ == '__main__':
    print(f"Total articles: {count_articles()}")