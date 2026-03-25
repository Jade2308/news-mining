#!/usr/bin/env python3
"""
scripts/seed_db.py – Crawl + làm sạch + lưu bài vào DB.

Cách dùng:
    python scripts/seed_db.py --source vnexpress --category kinh-doanh --limit 50
    python scripts/seed_db.py --source tuoitre   --category thoi-su    --limit 50
    python scripts/seed_db.py --source all       --limit 100

Rate-limit notes
----------------
* VNExpress: 1 s giữa mỗi bài.
* Tuổi Trẻ : 0.5 s giữa mỗi bài.
Vui lòng tôn trọng ToS và không crawl quá nhanh.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings import DB_PATH
from core.settings import SOURCES
from database.models import init_db
from database.engine import insert_article
from crawlers._vnexpress import VNExpressCrawler
from crawlers._tuoitre import TuoitreCrawler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s – %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger('seed_db')

_CRAWLER_MAP = {
    'vnexpress': VNExpressCrawler,
    'tuoitre': TuoitreCrawler,
}

def _categories_for_source(source: str, category: str | None) -> list[str]:
    """Resolve categories to crawl for one source."""
    if category:
        return [category]

    # If user does not pass --category, crawl all configured categories
    return list(SOURCES[source]['categories'].keys())


def seed(source: str, category: str | None, limit: int, db_path: str):
    CrawlerClass = _CRAWLER_MAP[source]
    categories = _categories_for_source(source, category)
    logger.info(f"[{source}] categories={categories}, limit(each)={limit}, db={db_path}")

    inserted = skipped_url = skipped_fp = 0

    for cat in categories:
        crawler = CrawlerClass(category=cat)
        articles = crawler.run()

        # Respect --limit per category
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


def main():
    parser = argparse.ArgumentParser(
        description='Crawl và lưu bài báo vào SQLite DB.'
    )
    parser.add_argument(
        '--source',
        choices=['vnexpress', 'tuoitre', 'all'],
        default='all',
        help='Nguồn cần crawl (mặc định: all)',
    )
    parser.add_argument(
        '--category',
        default=None,
        help='Chuyên mục cần crawl. Nếu bỏ trống sẽ crawl tất cả chuyên mục của nguồn.',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Số bài tối đa mỗi nguồn (mặc định: 50)',
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f'Đường dẫn DB (mặc định: {DB_PATH})',
    )
    args = parser.parse_args()

    # Auto-init DB if not present
    init_db(db_path=args.db_path)

    sources = list(_CRAWLER_MAP.keys()) if args.source == 'all' else [args.source]

    total_inserted = 0
    for src in sources:
        ins, _, _ = seed(src, args.category, args.limit, args.db_path)
        total_inserted += ins

    logger.info(f"Total inserted across all sources: {total_inserted}")


if __name__ == '__main__':
    main()
