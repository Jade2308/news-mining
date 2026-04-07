#!/usr/bin/env python3
"""
scripts/crawl_all.py
Crawl tất cả báo, tất cả chuyên mục và lưu vào database
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
import logging
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_news.crawlers.baomoi_crawler import BaomoiCrawler
from ai_news.crawlers.tuoitre_crawler import TuoitreCrawler
from ai_news.crawlers.vnexpress_crawler import VNExpressCrawler
from ai_news.crawlers.vietnamnet_crawler import VietnamNetCrawler
from ai_news.database.schema import init_db
from scripts.label_articles_with_predictions import run_labeling

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def crawl_newspaper(crawler_class, newspaper_name):
    """Crawl một báo tất cả chuyên mục"""
    logger.info(f"\n{'='*70}")
    logger.info(f"CRAWLING {newspaper_name.upper()}")
    logger.info(f"{'='*70}")
    
    crawler = crawler_class()
    total_articles = []
    
    categories = list(crawler.category_urls.keys())
    logger.info(f"Found {len(categories)} categories: {', '.join(categories)}")
    
    for i, category_slug in enumerate(categories, 1):
        logger.info(f"\n[{i}/{len(categories)}] Category: {category_slug}")
        
        try:
            crawler.category = category_slug
            articles = crawler.run()
            
            if articles:
                total_articles.extend(articles)
                logger.info(f"✅ Crawled {len(articles)} articles from {category_slug}")
            else:
                logger.warning(f"⚠️  No articles found in {category_slug}")
            
            time.sleep(3)  # Delay giữa các chuyên mục
            
        except Exception as e:
            logger.error(f"❌ Error crawling {category_slug}: {e}")
            continue
    
    # Lưu vào database
    if total_articles:
        logger.info(f"\n{'='*70}")
        logger.info(f"Saving {len(total_articles)} articles from {newspaper_name} to database...")
        saved = crawler.save_to_database(total_articles)
        logger.info(f"✅ Saved {saved} articles from {newspaper_name}")
    else:
        logger.warning(f"⚠️  No articles to save from {newspaper_name}")
    
    return len(total_articles)


def main():
    """Main function"""
    logger.info("="*70)
    logger.info("STARTING COMPREHENSIVE NEWS CRAWL")
    logger.info("="*70)
    
    # Initialize database
    logger.info("\nInitializing database...")
    init_db()
    
    # Crawl all newspapers
    crawlers = [
        (TuoitreCrawler, 'tuoitre'),
        (VNExpressCrawler, 'vnexpress'),
        (VietnamNetCrawler, 'vietnamnet'),
    ]
    
    total_all = 0
    results = {}
    
    for crawler_class, newspaper_name in crawlers:
        try:
            count = crawl_newspaper(crawler_class, newspaper_name)
            results[newspaper_name] = count
            total_all += count
            
            # Delay giữa các báo
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Error crawling {newspaper_name}: {e}", exc_info=True)
            results[newspaper_name] = 0
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("CRAWL SUMMARY")
    logger.info(f"{'='*70}")
    
    for newspaper, count in results.items():
        logger.info(f"{newspaper:15} : {count:5} articles")
    
    logger.info(f"{'-'*70}")
    logger.info(f"{'TOTAL':15} : {total_all:5} articles")
    logger.info(f"{'='*70}")
    
    logger.info("✅ Crawl completed successfully!")

    logger.info("\nStarting automatic labeling after crawl...")
    run_labeling(
        model_path='models/phobert_clickbait',
        model_version='phobert_v1.0',
        batch_size=32,
        show_samples=False,
    )


if __name__ == '__main__':
    main()
