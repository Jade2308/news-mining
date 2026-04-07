import re
import time
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from ai_news.crawlers.base_crawler import BaseCrawler
from ai_news.crawlers.utils import normalize_text, parse_time
from ai_news.core.types import Article
from ai_news.processing.clean_text import extract_text_from_html, clean_text

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))
_ARTICLE_URL_RE = re.compile(r'-c\d+\.epi$')


class BaomoiCrawler(BaseCrawler):
    """Crawler cho baomoi.com"""
    
    def __init__(self, category='trang-chu'):
        super().__init__('baomoi', category)
        self.base_url = 'https://www.baomoi.com'
        
        # Mapping category -> URL
        self.category_urls = {
            'trang-chu': 'https://www.baomoi.com',
            'bong-đa': 'https://www.baomoi.com/bong-da.epi',
            'the-gioi': 'https://www.baomoi.com/the-gioi.epi',
            'xa-hoi': 'https://www.baomoi.com/xa-hoi.epi',
            'van-hoa': 'https://www.baomoi.com/van-hoa.epi',
            'kinh-te': 'https://www.baomoi.com/kinh-te.epi',
            'giao-duc': 'https://www.baomoi.com/giao-duc.epi',
            'the-thao': 'https://www.baomoi.com/the-thao.epi',
            'giai-tri': 'https://www.baomoi.com/giai-tri.epi',
            'phap-luat': 'https://www.baomoi.com/phap-luat.epi',
            'cong-nghe': 'https://baomoi.com/khoa-hoc-cong-nghe.epi',
            'khoa-hoc': 'https://baomoi.com/khoa-hoc.epi',
            'doi-song': 'https://www.baomoi.com/doi-song.epi',
            'xe-co': 'https://www.baomoi.com/xe-co.epi',
            'nha-dat': 'https://www.baomoi.com/nha-dat.epi',
        }
    def fetch_listing(self):
        """Lấy danh sách URL bài từ baomoi.com"""
        url = self.category_urls.get(self.category) or self.category_urls.get('trang-chu') or self.base_url
        logger.info(f"Fetching listing from {url}")
        
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')
            
            urls = []
            seen = set()

            # Baomoi hiện dùng slug bài viết dạng: ...-c54849004.epi
            # Duyệt tất cả anchor rồi lọc theo pattern bài viết thực
            article_links = soup.select('a[href]')

            blacklist_patterns = [
                '/tag/', '/tim-kiem', '/video', '/photo', '/comment',
                '/tin-video', '/tin-anh', '/chu-de', '/livescore', '/top'
            ]

            for a in article_links:
                href = a.get('href', '').strip()
                if not href:
                    continue
                
                # Xử lý URL tương đối
                full_url = urljoin(self.base_url, href)
                
                # Kiểm tra xem có phải URL hợp lệ không
                if not full_url.startswith(self.base_url):
                    continue
                
                # Loại bỏ các URL không phải bài viết
                if any(pattern in full_url for pattern in blacklist_patterns):
                    continue

                # Chỉ nhận bài viết thật sự
                if not _ARTICLE_URL_RE.search(full_url):
                    continue
                
                # Loại bỏ URL trùng lặp
                if full_url in seen:
                    continue
                
                # Loại bỏ URL quảng cáo hoặc trang chính
                if full_url.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
                    continue
                
                seen.add(full_url)
                urls.append(full_url)
                
                if len(urls) >= 50:
                    break
            
            logger.info(f"Found {len(urls)} article URLs")
            return urls
            
        except Exception as e:
            logger.error(f"Error fetching listing: {e}", exc_info=True)
            return []
    
    def parse_article(self, url):
        """Parse chi tiết một bài viết từ baomoi.com"""
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Lấy tiêu đề
            title = None
            title_selectors = [
                'h1.title-detail',
                'h1.article-title',
                'h1',
                'meta[property="og:title"]',
            ]
            
            for sel in title_selectors:
                if sel.startswith('meta'):
                    meta = soup.select_one(sel)
                    if meta:
                        title = meta.get('content', '').strip()
                        break
                else:
                    elem = soup.select_one(sel)
                    if elem:
                        title = elem.get_text(strip=True)
                        break
            
            if not title:
                logger.warning(f"Could not find title for {url}")
                return None
            
            # Lấy mô tả ngắn
            description = None
            desc_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                'p.description',
                'p.lead',
                '.article-description',
            ]
            
            for sel in desc_selectors:
                elem = soup.select_one(sel)
                if elem:
                    if sel.startswith('meta'):
                        description = elem.get('content', '').strip()
                    else:
                        description = elem.get_text(strip=True)
                    if description:
                        break
            
            # Lấy nội dung bài viết
            content = None
            content_selectors = [
                'div.detail-content',
                'div.article-content',
                'div.content-news',
                'article',
                '.news-detail-content',
            ]
            
            for sel in content_selectors:
                elem = soup.select_one(sel)
                if elem:
                    content = elem.decode_contents()
                    break
            
            if not content:
                logger.warning(f"Could not find content for {url}")
                return None
            
            # Trích xuất text từ HTML
            text_content = extract_text_from_html(content)
            text_content = clean_text(text_content)
            
            if not text_content:
                logger.warning(f"No text content extracted for {url}")
                return None
            
            # Lấy thời gian đăng
            publish_time = None
            time_selectors = [
                'span.publish-time',
                'span.time-publish',
                'time',
                'meta[property="article:published_time"]',
                '.article-time',
                '.publish-time',
            ]
            
            for sel in time_selectors:
                if sel.startswith('meta'):
                    elem = soup.select_one(sel)
                    if elem:
                        time_str = elem.get('content', '').strip()
                else:
                    elem = soup.select_one(sel)
                    if elem:
                        time_str = elem.get_text(strip=True) if not sel.startswith('time') else elem.get('datetime', '')
                
                if time_str:
                    parsed = parse_time(time_str)
                    if parsed:
                        publish_time = parsed
                        break
            
            # Nếu không tìm được, dùng thời gian hiện tại
            if not publish_time:
                publish_time = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')
            
            # Lấy tác giả
            author = None
            author_selectors = [
                'span.author-name',
                'a.author-link',
                '.article-author',
                'meta[name="author"]',
            ]
            
            for sel in author_selectors:
                if sel.startswith('meta'):
                    elem = soup.select_one(sel)
                    if elem:
                        author = elem.get('content', '').strip()
                else:
                    elem = soup.select_one(sel)
                    if elem:
                        author = elem.get_text(strip=True)
                if author:
                    break
            
            # Tạo object Article
            article = Article(
                source=self.source,
                category=self.category,
                title=normalize_text(title),
                description=normalize_text(description) if description else '',
                content=text_content,
                author=author or 'Unknown',
                publish_time=publish_time,
                url=url,
                crawl_time=datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S'),
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Error parsing article {url}: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    # Test crawler - crawl tất cả chuyên mục
    crawler = BaomoiCrawler()
    
    total_articles = []
    for category_slug in crawler.category_urls.keys():
        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling category: {category_slug}")
        logger.info(f"{'='*60}")
        
        crawler.category = category_slug
        articles = crawler.run()
        total_articles.extend(articles)
        time.sleep(2)  # Delay giữa các chuyên mục
    
    # Lưu vào database
    logger.info(f"\n{'='*60}")
    logger.info(f"Total articles crawled: {len(total_articles)}")
    logger.info(f"Saving to database...")
    crawler.save_to_database(total_articles)
    logger.info(f"✅ Done!")

