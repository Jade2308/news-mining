import time
import logging
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

from crawlers.base_crawler import BaseCrawler
from crawlers.utils import normalize_text, parse_time
from core.types import Article
from core.clean_text import extract_text_from_html, clean_text

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))

class VietnamNetCrawler(BaseCrawler):
    def __init__(self, category='thoi-su'):
        super().__init__('vietnamnet', category)
        self.base_url = 'https://vietnamnet.vn'

        self.category_urls = {
            'chinh-tri': 'https://vietnamnet.vn/chinh-tri',
            'thoi-su': 'https://vietnamnet.vn/thoi-su',
            'net-zero': 'https://vietnamnet.vn/net-zero',
            'giao-duc': 'https://vietnamnet.vn/giao-duc',
            'the-gioi': 'https://vietnamnet.vn/the-gioi',
            'the-thao': 'https://vietnamnet.vn/the-thao',
            'đoi-song': 'https://vietnamnet.vn/doi-song',
            'tuan-viet-nam': 'https://vietnamnet.vn/tuan-viet-nam',
            'suc-khoe': 'https://vietnamnet.vn/suc-khoe',
            'cong-nghe': 'https://vietnamnet.vn/cong-nghe',
            'phap-luat': 'https://vietnamnet.vn/phap-luat',
            'xe': 'https://vietnamnet.vn/oto-xe-may',
            'bat-đong-san': 'https://vietnamnet.vn/bat-dong-san',
            'du-lich': 'https://vietnamnet.vn/du-lich',
            'ban-đoc': 'https://vietnamnet.vn/ban-doc',
        }

    def fetch_listing(self):
        url = self.category_urls.get(self.category, f'{self.base_url}/{self.category}')
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            # Vietnamnet articles are often split into different wrapper divs like vnn-title, feature-box
            urls = []
            # Try to grab anchors with href inside heading tags
            for link in soup.select('h3 a, h2 a, h4 a, .vnn-title a'):
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = self.base_url + href
                    if href not in urls:
                        urls.append(href)

            logger.info(f"Found {len(urls)} article items")
            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return []

    def parse_article(self, url):
        time.sleep(1)

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text
            soup = BeautifulSoup(r.content, 'html.parser')

            # --- Title ---
            # VietnamNet uses <h1 class="content-detail-title">
            title_elem = soup.select_one('h1.content-detail-title, h1.title')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"No title found for {url}, skipping")
                return None

            # --- Summary ---
            summary_elem = soup.select_one('h2.content-detail-sapo, div.content-detail-sapo')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            # --- Author ---
            # VietnamNet doesn't reliably have an author or uses something like <span class="author-name">
            author_elem = soup.select_one('p.author-name, span.author, .author-info a')
            author = normalize_text(author_elem.get_text()) if author_elem else None

            # --- Tags ---
            tag_elems = soup.select('div.tags-box a.tag, div.tags a')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            # --- Content ---
            content_elem = soup.select_one('div.maincontent, div.content-detail')
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or html,
                content_selector='div.maincontent, div.content-detail',
            )
            content_text = clean_text(content_text)

            # --- Published time ---
            # Typically <div class="bread-crumb-detail__time">
            time_elem = soup.select_one('.bread-crumb-detail__time, .publish-time')
            published_at = None
            if time_elem:
                published_at = parse_time(normalize_text(time_elem.get_text()))

            crawled_at = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

            return Article(
                url=url,
                source='vietnamnet',
                category=self.category,
                title=title,
                summary=summary or None,
                content_text=content_text,
                author=author,
                tags=tags,
                published_at=published_at,
                crawled_at=crawled_at,
                content_html_raw=content_html_raw or None,
            ).to_dict()

        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None

if __name__ == '__main__':
    crawler_instance = VietnamNetCrawler()
    
    total_articles = []
    for category_slug in crawler_instance.category_urls.keys():
        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling category: {category_slug}")
        logger.info(f"{'='*60}")
        
        crawler_instance.category = category_slug
        articles = crawler_instance.run()
        total_articles.extend(articles)
        time.sleep(2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Total articles crawled: {len(total_articles)}")
    logger.info(f"Saving to database...")
    crawler_instance.save_to_database(total_articles)
    logger.info(f"✅ Done!")
