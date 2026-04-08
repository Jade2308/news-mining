#!/usr/bin/env python3
"""
scripts/db_tool.py – Công cụ quản lý cơ sở dữ liệu (Khởi tạo, Seed, Kiểm tra).

Các lệnh hỗ trợ:
    python scripts/db_tool.py init [--db-path PATH]
    python scripts/db_tool.py seed [--source {vnexpress,tuoitre,all}] [--category CAT] [--limit N] [--db-path PATH]
    python scripts/db_tool.py check [--db-path PATH]
"""

import argparse
import logging
import os
import sys
import sqlite3
from pathlib import Path

# Fix imports for the new project structure
import sys
import os
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import DB_PATH, SOURCES
from database.schema import init_db
from database.db import insert_article
from crawlers.vnexpress_crawler import VNExpressCrawler
from crawlers.tuoitre_crawler import TuoitreCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s – %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('db_tool')

_CRAWLER_MAP = {
    'vnexpress': VNExpressCrawler,
    'tuoitre': TuoitreCrawler,
}

def _categories_for_source(source: str, category: str | None) -> list[str]:
    """Resolve categories to crawl for one source."""
    if category:
        return [category]
    return list(SOURCES[source]['categories'].keys())

def seed(source: str, category: str | None, limit: int, db_path: str):
    CrawlerClass = _CRAWLER_MAP[source]
    categories = _categories_for_source(source, category)
    logger.info(f"[{source}] categories={categories}, limit(each)={limit}, db={db_path}")

    inserted = skipped_url = skipped_fp = 0

    for cat in categories:
        crawler = CrawlerClass(category=cat)
        articles = crawler.run()

        if limit and len(articles) > limit:
            articles = articles[:limit]

        cat_inserted = cat_skipped_url = cat_skipped_fp = 0
        for art in articles:
            if not art:
                continue
            result = insert_article(art, db_path=db_path)
            if result == 'inserted':
                inserted += 1
                cat_inserted += 1
            elif result == 'dup_url':
                skipped_url += 1
                cat_skipped_url += 1
            elif result == 'dup_fp':
                skipped_fp += 1
                cat_skipped_fp += 1

        logger.info(
            f"[{source}/{cat}] Done – inserted={cat_inserted}, "
            f"skip_url={cat_skipped_url}, skip_fp(content_dup)={cat_skipped_fp}"
        )

    logger.info(
        f"[{source}] Total – inserted={inserted}, "
        f"skip_url={skipped_url}, skip_fp(content_dup)={skipped_fp}"
    )
    return inserted, skipped_url, skipped_fp

def check_database(db_path: str):
    """Kiểm tra trạng thái database"""
    print(f"\n{'='*70}")
    print(f"DATABASE CHECK")
    print(f"{'='*70}")
    print(f"\nDatabase path: {db_path}")
    
    if os.path.exists(db_path):
        size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        print(f"✅ Database file exists ({size:.2f} MB)")
    else:
        print(f"❌ Database file does NOT exist")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        if cursor.fetchone():
            print(f"✅ Table 'articles' exists")
        else:
            print(f"❌ Table 'articles' NOT found")
            return
        
        cursor.execute('SELECT COUNT(*) FROM articles')
        total = cursor.fetchone()[0]
        print(f"✅ Total articles: {total}")
        
        if total == 0:
            print(f"\n⚠️  Database is empty.")
            conn.close()
            return
        
        cursor.execute('SELECT source, COUNT(*) as count FROM articles GROUP BY source')
        sources = cursor.fetchall()
        print(f"\nArticles by source:")
        for source, count in sources:
            print(f"  - {source:<20}: {count:>5}")
        
        cursor.execute('SELECT category, COUNT(*) as count FROM articles GROUP BY category ORDER BY count DESC LIMIT 10')
        categories = cursor.fetchall()
        print(f"\nTop 10 categories:")
        for category, count in categories:
            print(f"  - {category:<30}: {count:>5}")
        
        cursor.execute('SELECT title, source, published_at, crawled_at FROM articles ORDER BY crawled_at DESC LIMIT 3')
        latest = cursor.fetchall()
        print(f"\nLatest 3 articles:")
        for i, (title, source, pub, crawl) in enumerate(latest, 1):
            print(f"  [{i}] {title[:60]}...")
            print(f"      Source: {source}, Published: {pub}, Crawled: {crawl}")
        
        conn.close()
        print(f"\n✅ Database is in good condition!")
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")

def main():
    parser = argparse.ArgumentParser(description='Công cụ quản lý SQLite database cho news-mining.')
    subparsers = parser.add_subparsers(dest='command', help='Các lệnh: init, seed, check')

    # init
    init_parser = subparsers.add_parser('init', help='Khởi tạo database')
    init_parser.add_argument('--db-path', default=DB_PATH, help=f'Đường dẫn DB (mặc định: {DB_PATH})')

    # seed
    seed_parser = subparsers.add_parser('seed', help='Crawl và lưu bài báo mồi vào DB')
    seed_parser.add_argument('--source', choices=['vnexpress', 'tuoitre', 'all'], default='all', help='Nguồn crawl')
    seed_parser.add_argument('--category', default=None, help='Chuyên mục crawl')
    seed_parser.add_argument('--limit', type=int, default=50, help='Số bài tối đa mỗi nguồn')
    seed_parser.add_argument('--db-path', default=DB_PATH, help=f'Đường dẫn DB (mặc định: {DB_PATH})')

    # check
    check_parser = subparsers.add_parser('check', help='Kiểm tra trạng thái database')
    check_parser.add_argument('--db-path', default=DB_PATH, help=f'Đường dẫn DB (mặc định: {DB_PATH})')

    args = parser.parse_args()

    if args.command == 'init':
        init_db(db_path=args.db_path)
    elif args.command == 'seed':
        init_db(db_path=args.db_path)
        sources = list(_CRAWLER_MAP.keys()) if args.source == 'all' else [args.source]
        total_inserted = 0
        for src in sources:
            ins, _, _ = seed(src, args.category, args.limit, args.db_path)
            total_inserted += ins
        logger.info(f"Total inserted across all sources: {total_inserted}")
    elif args.command == 'check':
        check_database(args.db_path)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
