# database/schema.py
import sqlite3
from datetime import datetime

DB_PATH = 'news.db'

def init_db():
    """Khởi tạo database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        source TEXT NOT NULL,              -- 'vnexpress', 'tuoitre'
        category TEXT,                     -- 'kinh-doanh', 'cong-nghe'...
        title TEXT NOT NULL,
        summary TEXT,
        content TEXT,
        published_at DATETIME,             -- ⭐ thời gian đăng (dùng lọc)
        crawled_at DATETIME NOT NULL,      -- thời gian crawl
        clickbait_score REAL DEFAULT 0,    -- 0-1
        clickbait_label INTEGER,           -- 0/1
        topic_id INTEGER,                  -- chủ đề
        topic_version TEXT,                -- batch version
        is_featured BOOLEAN DEFAULT 0,     -- có ở top không
        featured_position INTEGER,         -- vị trí bao nhiêu
        featured_since DATETIME,           -- lúc nào ở top
        featured_duration_hours REAL,      -- bao lâu ở top
        view_count INTEGER,                -- lượt xem
        trending_score REAL DEFAULT 0,     -- điểm trending
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

if __name__ == '__main__':
    init_db()