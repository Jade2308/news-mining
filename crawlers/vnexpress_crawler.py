# crawlers/vnexpress_crawler.py
import requests
from bs4 import BeautifulSoup
from crawlers.base_crawler import BaseCrawler
from crawlers.utils import normalize_text, parse_relative_time
import logging
import time

logger = logging.getLogger(__name__)

class VNExpressCrawler(BaseCrawler):
    def __init__(self, category='kinh-doanh'):
        super().__init__('vnexpress', category)
        self.base_url = 'https://vnexpress.net'
    
    def fetch_listing(self):
        """Lấy danh sách URL từ trang chuyên mục"""
        url = f'{self.base_url}/{self.category}'
        logger.info(f"Fetching listing from {url}")
        
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Tìm các article item (tuỳ cấu trúc site)
            articles = soup.select('article.item-news')
            logger.info(f"Found {len(articles)} article items")
            
            urls = []
            for article in articles[:50]:  # Lấy top 50 để test
                link = article.select_one('a.title-news, h3 a')
                if link and link.get('href'):
                    url = link['href']
                    # Đảm bảo URL đầy đủ
                    if not url.startswith('http'):
                        url = self.base_url + url
                    urls.append(url)
            
            return urls
        
        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return []
    
    def parse_article(self, url):
        """Parse 1 bài"""
        time.sleep(1)  # Throttle
        
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Trích xuất dữ liệu
            title_elem = soup.select_one('h1.title-detail')
            title = normalize_text(title_elem.text) if title_elem else 'N/A'
            
            summary_elem = soup.select_one('p.description')
            summary = normalize_text(summary_elem.text) if summary_elem else ''
            
            # Content
            content_elem = soup.select_one('article')
            content = ''
            if content_elem:
                # Lấy text của tất cả paragraph
                paragraphs = content_elem.select('p')
                content = ' '.join([p.text for p in paragraphs[:10]])  # Top 10 para
            
            # Thời gian
            time_elem = soup.select_one('span.date')
            published_at = None
            if time_elem:
                time_text = normalize_text(time_elem.text)
                published_at = parse_relative_time(time_text)
            
            return {
                'url': url,
                'source': 'vnexpress',
                'category': self.category,
                'title': title,
                'summary': summary,
                'content': content[:500],  # Lưu top 500 char
                'published_at': published_at,
            }
        
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

if __name__ == '__main__':
    crawler = VNExpressCrawler(category='kinh-doanh')
    articles = crawler.run()
    print(f"Crawled {len(articles)} articles")
    if articles:
        print(articles[0])