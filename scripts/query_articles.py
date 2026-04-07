#!/usr/bin/env python3
"""
scripts/query_articles.py
Query dữ liệu từ database
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
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_news.config import DB_PATH


def print_stats():
    """In ra thống kê chung"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Tổng số bài
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        
        # Số bài theo nguồn
        cursor.execute('''
        SELECT source, COUNT(*) as count 
        FROM articles 
        GROUP BY source
        ''')
        by_source = cursor.fetchall()
        
        # Số bài theo chuyên mục
        cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        GROUP BY category 
        ORDER BY count DESC
        ''')
        by_category = cursor.fetchall()
        
        print("\n" + "="*70)
        print("DATABASE STATISTICS")
        print("="*70)
        
        print(f"\nTotal articles: {total}")
        
        print(f"\n{'Source':<20} {'Count':>10}")
        print("-"*30)
        for source, count in by_source:
            print(f"{source:<20} {count:>10}")
        
        print(f"\n{'Category':<30} {'Count':>10}")
        print("-"*40)
        for category, count in by_category:
            print(f"{category:<30} {count:>10}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")


def get_articles(category=None, source=None, limit=10):
    """Lấy danh sách bài viết"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM articles WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if source:
            query += ' AND source = ?'
            params.append(source)
        
        query += ' ORDER BY published_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        
        print(f"\n{'='*100}")
        print(f"ARTICLES (limit: {limit})")
        if category:
            print(f"Category: {category}")
        if source:
            print(f"Source: {source}")
        print(f"{'='*100}")
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['source']} - {article['category']}")
            print(f"Title: {article['title'][:80]}")
            print(f"Published: {article['published_at']}")
            print(f"Author: {article['author'] or 'N/A'}")
            print(f"Tags: {article['tags'] or 'N/A'}")
            print(f"URL: {article['url'][:60]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")


def get_latest_articles(limit=5):
    """Lấy bài viết mới nhất"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM articles 
        ORDER BY published_at DESC LIMIT ?
        ''', (limit,))
        
        articles = cursor.fetchall()
        
        print(f"\n{'='*100}")
        print(f"LATEST ARTICLES")
        print(f"{'='*100}")
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['published_at']}")
            print(f"Source: {article['source']} | Category: {article['category']}")
            print(f"Title: {article['title'][:90]}")
            print(f"Content preview: {article['content_text'][:100]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")


def search_articles(keyword, limit=10):
    """Tìm kiếm bài viết theo từ khóa"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_term = f"%{keyword}%"
        cursor.execute('''
        SELECT * FROM articles 
        WHERE title LIKE ? OR content_text LIKE ? OR summary LIKE ?
        ORDER BY published_at DESC LIMIT ?
        ''', (search_term, search_term, search_term, limit))
        
        articles = cursor.fetchall()
        
        print(f"\n{'='*100}")
        print(f"SEARCH RESULTS FOR: '{keyword}' ({len(articles)} found)")
        print(f"{'='*100}")
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article['source']} - {article['category']}")
            print(f"Title: {article['title'][:80]}")
            print(f"Published: {article['published_at']}")
            print(f"Match: {article['content_text'][:100]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    print_stats()
    print("\n" + "="*70)
    print("EXAMPLES:")
    print("="*70)
    
    get_latest_articles(limit=5)
    
    # search_articles('Việt Nam', limit=5)
