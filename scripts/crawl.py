#!/usr/bin/env python3
"""
scripts/crawl.py – Thu thập tin tức từ nhiều nguồn báo khác nhau.

Các lệnh hỗ trợ:
    python scripts/crawl.py --full     (Mẫu cũ: crawl_all.py)
    python scripts/crawl.py --hourly   (Mẫu cũ: crawl_hourly.py)
"""

import argparse
import logging
import os
import sys
import time
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

from crawlers.tuoitre_crawler import TuoitreCrawler
from crawlers.vnexpress_crawler import VNExpressCrawler
from crawlers.vietnamnet_crawler import VietnamNetCrawler
from database.schema import init_db
from scripts.label_articles import run_labeling

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def crawl_newspaper(crawler_class, newspaper_name, mode='full', max_articles=10, stop_on_duplicate=True):
    """Crawl một báo tất cả chuyên mục"""
    logger.info(f"\n{'='*70}")
    logger.info(f"{mode.upper()} CRAWLING {newspaper_name.upper()}")
    logger.info(f"{'='*70}")
    
    crawler = crawler_class()
    total_articles = []
    
    categories = list(crawler.category_urls.keys())
    logger.info(f"Found {len(categories)} categories: {', '.join(categories)}")
    
    for i, category_slug in enumerate(categories, 1):
        logger.info(f"\n[{i}/{len(categories)}] Category: {category_slug}")
        
        try:
            crawler.category = category_slug
            if mode == 'hourly':
                articles = crawler.run(max_articles=max_articles, stop_on_duplicate=stop_on_duplicate)
            else:
                articles = crawler.run()
            
            if articles:
                total_articles.extend(articles)
                logger.info(f"✅ Crawled {len(articles)} articles from {category_slug}")
            else:
                if mode == 'hourly':
                    logger.info(f"⏭️ No new articles found in {category_slug} (all were skipped)")
                else:
                    logger.warning(f"⚠️ No articles found in {category_slug}")
            
            time.sleep(1 if mode == 'hourly' else 3)
            
        except Exception as e:
            logger.error(f"❌ Error crawling {category_slug}: {e}")
            continue
    
    if total_articles:
        logger.info(f"\nSaved {len(total_articles)} articles from {newspaper_name} to database...")
        saved = crawler.save_to_database(total_articles)
        logger.info(f"✅ Saved {saved} articles from {newspaper_name}")
    else:
        logger.info(f"✅ No articles found from {newspaper_name} that need saving.")
    
    return len(total_articles)

def main():
    parser = argparse.ArgumentParser(description='Thu thập tin tức từ nhiều nguồn.')
    parser.add_argument('--full', action='store_true', help='Crawl đầy đủ tất cả các bài trên chuyên mục')
    parser.add_argument('--hourly', action='store_true', help='Crawl nhanh theo giờ (giới hạn bài báo mới)')
    parser.add_argument('--max-articles', type=int, default=10, help='Số bài tối đa mỗi chuyên mục (chỉ dùng cho --hourly)')
    
    args = parser.parse_args()

    if not args.full and not args.hourly:
        logger.warning("Cần chọn chế độ: --full hoặc --hourly. Mặc định dùng --hourly.")
        args.hourly = True

    mode = 'full' if args.full else 'hourly'
    
    logger.info("="*70)
    logger.info(f"STARTING {mode.upper()} NEWS CRAWL")
    logger.info("="*70)
    
    init_db()
    
    crawlers = [
        (TuoitreCrawler, 'tuoitre'),
        (VNExpressCrawler, 'vnexpress'),
        (VietnamNetCrawler, 'vietnamnet'),
    ]
    
    total_all = 0
    results = {}
    
    for crawler_class, newspaper_name in crawlers:
        try:
            count = crawl_newspaper(
                crawler_class, newspaper_name, mode=mode,
                max_articles=args.max_articles, stop_on_duplicate=True if mode == 'hourly' else False
            )
            results[newspaper_name] = count
            total_all += count
            time.sleep(2 if mode == 'hourly' else 5)
        except Exception as e:
            logger.error(f"❌ Error crawling {newspaper_name}: {e}")
            results[newspaper_name] = 0
    
    logger.info(f"\n{'='*70}\nCRAWL SUMMARY\n{'='*70}")
    for newspaper, count in results.items():
        logger.info(f"{newspaper:15} : {count:5} articles")
    logger.info(f"{'-'*70}\n{'TOTAL':15} : {total_all:5} articles\n{'='*70}")
    
    if total_all > 0:
        logger.info("\nStarting automatic labeling for new articles...")
        run_labeling(
            model_path='models/phobert_clickbait',
            model_version='phobert_v1.0',
            batch_size=32,
            show_samples=False,
        )
    else:
        logger.info("\n✅ No new articles found. Skipping AI Predictions.")

if __name__ == '__main__':
    main()
