# crawlers/base_crawler.py
import requests
from bs4 import BeautifulSoup
import logging
from abc import ABC, abstractmethod
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseCrawler(ABC):
    """Base class cho tất cả crawler"""
    
    def __init__(self, source_name, category):
        self.source = source_name
        self.category = category
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    @abstractmethod
    def fetch_listing(self):
        """Lấy danh sách URL bài mới - cần override"""
        raise NotImplementedError
    
    @abstractmethod
    def parse_article(self, url):
        """Parse 1 bài - cần override"""
        raise NotImplementedError
    
    def run(self):
        """Orchestrate: fetch listing → parse từng bài"""
        logger.info(f"Starting crawl for {self.source} - {self.category}")
        
        try:
            listing = self.fetch_listing()
            logger.info(f"Found {len(listing)} articles in listing")
            
            articles = []
            for i, url in enumerate(listing, 1):
                try:
                    article = self.parse_article(url)
                    if article:
                        articles.append(article)
                        logger.info(f"✅ Parsed {i}/{len(listing)}: {article['title'][:50]}")
                except Exception as e:
                    logger.error(f"❌ Error parsing {url}: {e}")
                    continue
            
            logger.info(f"✅ Crawl completed: {len(articles)} articles parsed")
            return articles
        
        except Exception as e:
            logger.error(f"❌ Crawl failed: {e}")
            return []

if __name__ == '__main__':
    pass