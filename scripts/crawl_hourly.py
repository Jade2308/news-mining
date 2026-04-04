#!/usr/bin/env python3
"""
scripts/crawl_hourly.py
Crawl chế độ siêu tốc định kỳ mỗi giờ: chỉ lấy vài bài mới nhất và dừng ngay khi thấy bài cũ.
"""

import sys
import os
import logging
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.baomoi_crawler import BaomoiCrawler
from crawlers.tuoitre_crawler import TuoitreCrawler
from crawlers.vnexpress_crawler import VNExpressCrawler
from crawlers.vietnamnet_crawler import VietnamNetCrawler
from database.schema import init_db
from scripts.label_articles_with_predictions import run_labeling

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def crawl_newspaper(crawler_class, newspaper_name, max_articles=10, stop_on_duplicate=True):
    """Crawl một báo tất cả chuyên mục (Chế độ Hourly)"""
    logger.info(f"\n{'='*70}")
    logger.info(f"HOURLY CRAWLING {newspaper_name.upper()}")
    logger.info(f"{'='*70}")
    
    crawler = crawler_class()
    total_articles = []
    
    categories = list(crawler.category_urls.keys())
    logger.info(f"Found {len(categories)} categories: {', '.join(categories)}")
    
    for i, category_slug in enumerate(categories, 1):
        logger.info(f"\n[{i}/{len(categories)}] Category: {category_slug}")
        
        try:
            crawler.category = category_slug
            # DÙNG PARAM GIỚI HẠN: max_articles và stop_on_duplicate
            articles = crawler.run(max_articles=max_articles, stop_on_duplicate=stop_on_duplicate)
            
            if articles:
                total_articles.extend(articles)
                logger.info(f"✅ Crawled {len(articles)} new articles from {category_slug}")
            else:
                logger.info(f"⏭️ No new articles found in {category_slug} (all were skipped)")
            
            time.sleep(1)  # Delay ngắn gọn hơn so với crawl_all
            
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
        logger.info(f"✅ Không có bài mới nào từ {newspaper_name} cần lưu.")
    
    return len(total_articles)


def main():
    """Main function"""
    logger.info("="*70)
    logger.info("STARTING HOURLY QUICK CRAWL")
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
            # GỌI HÀM VỚI GIỚI HẠN CHO HOURLY (Chỉ lấy tối đa 10 bài mới nhất trên trang danh mục)
            # Và ngay lập tức ngừng chuyên mục đó nếu đụng phải ảnh bài gốc đã có sẵn (`stop_on_duplicate=True`)
            count = crawl_newspaper(crawler_class, newspaper_name, max_articles=10, stop_on_duplicate=True)
            results[newspaper_name] = count
            total_all += count
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Error crawling {newspaper_name}: {e}", exc_info=True)
            results[newspaper_name] = 0
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("HOURLY CRAWL SUMMARY")
    logger.info(f"{'='*70}")
    
    for newspaper, count in results.items():
        logger.info(f"{newspaper:15} : {count:5} new articles")
    
    logger.info(f"{'-'*70}")
    logger.info(f"{'TOTAL':15} : {total_all:5} new articles")
    logger.info(f"{'='*70}")
    
    logger.info("✅ Hourly crawl completed successfully!")

    # Cải tiến: Nếu không có bài mới, bỏ luôn bước bật Model Load cho nhẹ RAM và tiết kiệm thời gian
    if total_all > 0:
        logger.info("\nStarting automatic labeling for new articles...")
        run_labeling(
            model_path='models/phobert_clickbait',
            model_version='phobert_v1.0',
            batch_size=32,
            show_samples=False,
        )
    else:
        logger.info("\n✅ No new articles found. SKipping AI Predictions (Model won't load).")


if __name__ == '__main__':
    main()
