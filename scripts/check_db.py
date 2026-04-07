#!/usr/bin/env python3
"""
scripts/check_db.py
Kiểm tra trạng thái database
"""

import sys

# Fix imports for the new project structure
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_news.config import DB_PATH


def check_database():
    """Kiểm tra database"""
    print(f"\n{'='*70}")
    print(f"DATABASE CHECK")
    print(f"{'='*70}")
    print(f"\nDatabase path: {DB_PATH}")
    
    # Kiểm tra file tồn tại
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH) / (1024 * 1024)  # MB
        print(f"✅ Database file exists ({size:.2f} MB)")
    else:
        print(f"❌ Database file does NOT exist")
        print(f"Run: python scripts/crawl_all.py")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Kiểm tra table
        cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='articles'
        ''')
        
        if cursor.fetchone():
            print(f"✅ Table 'articles' exists")
        else:
            print(f"❌ Table 'articles' NOT found")
            return
        
        # Tổng số bài
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        print(f"✅ Total articles: {total}")
        
        if total == 0:
            print(f"\n⚠️  Database is empty. Run: python scripts/crawl_all.py")
            conn.close()
            return
        
        # Thống kê theo nguồn
        cursor.execute('''
        SELECT source, COUNT(*) as count 
        FROM articles 
        GROUP BY source
        ''')
        sources = cursor.fetchall()
        
        print(f"\nArticles by source:")
        for source, count in sources:
            print(f"  - {source:<20}: {count:>5}")
        
        # Thống kê theo chuyên mục
        cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        GROUP BY category 
        ORDER BY count DESC
        LIMIT 10
        ''')
        categories = cursor.fetchall()
        
        print(f"\nTop 10 categories:")
        for category, count in categories:
            print(f"  - {category:<30}: {count:>5}")
        
        # Bài viết mới nhất
        cursor.execute('''
        SELECT title, source, published_at, crawled_at
        FROM articles 
        ORDER BY crawled_at DESC 
        LIMIT 3
        ''')
        latest = cursor.fetchall()
        
        print(f"\nLatest 3 articles:")
        for i, (title, source, pub, crawl) in enumerate(latest, 1):
            print(f"  [{i}] {title[:60]}...")
            print(f"      Source: {source}, Published: {pub}, Crawled: {crawl}")
        
        conn.close()
        print(f"\n✅ Database is in good condition!")
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")


if __name__ == '__main__':
    check_database()
