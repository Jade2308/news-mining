# database/db.py
import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'news.db'

def get_connection():
    """Lấy kết nối DB"""
    return sqlite3.connect(DB_PATH)

def insert_article(data):
    """Thêm bài viết"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO articles (
            url, source, category, title, summary, content,
            published_at, crawled_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['url'],
            data['source'],
            data.get('category'),
            data['title'],
            data.get('summary'),
            data.get('content'),
            data.get('published_at'),
            datetime.now()
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # URL đã tồn tại
        return False
    finally:
        conn.close()

def get_all_articles(limit=1000):
    """Lấy tất cả bài"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM articles LIMIT ?', [limit])
    columns = [description[0] for description in cursor.description]
    
    articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return articles

def get_articles_by_timerange(hours=24, limit=1000):
    """Lấy bài trong N giờ gần nhất"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM articles
    WHERE published_at > datetime('now', '-' || ? || ' hour')
    ORDER BY published_at DESC
    LIMIT ?
    ''', [hours, limit])
    
    columns = [description[0] for description in cursor.description]
    articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return articles

def update_article(article_id, data):
    """Cập nhật bài viết"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tạo SET clause động
    fields = ', '.join([f'{k} = ?' for k in data.keys()])
    values = list(data.values()) + [article_id]
    
    cursor.execute(f'UPDATE articles SET {fields} WHERE id = ?', values)
    conn.commit()
    conn.close()

def count_articles():
    """Đếm tổng bài"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM articles')
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

if __name__ == '__main__':
    print(f"Total articles: {count_articles()}")