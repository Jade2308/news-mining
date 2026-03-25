# crawlers/vnexpress_crawler.py
import time
import logging
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from crawlers.helpers import normalize_text, parse_time
from core.shared_types import Article
from core.cleaner import extract_text_from_html, clean_text

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))


class VNExpressCrawler(BaseCrawler):
    def __init__(self, category='thoi-su'):
        super().__init__('vnexpress', category)
        self.base_url = 'https://vnexpress.net'

        # Mapping category chuẩn hóa -> URL thực tế của VNExpress
        self.category_urls = {
            'thoi-su': 'https://vnexpress.net/thoi-su',
            'kinh-doanh': 'https://vnexpress.net/kinh-doanh',
            'cong-nghe': 'https://vnexpress.net/khoa-hoc',
            'giai-tri': 'https://vnexpress.net/giai-tri',
            'the-thao': 'https://vnexpress.net/the-thao',
            'suc-khoe': 'https://vnexpress.net/suc-khoe',
        }

    def fetch_listing(self):
        """Lấy danh sách URL từ trang chuyên mục."""
        url = self.category_urls.get(self.category, f'{self.base_url}/{self.category}')
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            articles = soup.select('article.item-news')
            logger.info(f"Found {len(articles)} article items")

            urls = []
            for article in articles:
                link = article.select_one('a.title-news, h3 a, h2 a')
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = self.base_url + href
                    urls.append(href)

            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return []

    def parse_article(self, url):
        """Parse 1 bài VNExpress và trả về Article theo schema chuẩn."""
        time.sleep(1)  # rate-limit

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text
            soup = BeautifulSoup(r.content, 'html.parser')

            # --- Title (required) ---
            title_elem = soup.select_one('h1.title-detail')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"No title found for {url}, skipping")
                return None

            # --- Summary ---
            summary_elem = soup.select_one('p.description')
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            # --- Author ---
            author_elem = soup.select_one('p.author_mail strong, p.author strong, span.author')
            author = normalize_text(author_elem.get_text()) if author_elem else None

            # --- Tags ---
            tag_elems = soup.select('ul.list-tag a, div.tags a')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            # --- Content ---
            content_elem = soup.select_one('article.fck_detail, article')
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or html,
                content_selector='article.fck_detail',
            )
            content_text = clean_text(content_text)

            # --- Published time ---
            time_elem = soup.select_one('span.date')
            published_at = None
            if time_elem:
                published_at = parse_time(normalize_text(time_elem.get_text()))

            # --- Crawled at ---
            crawled_at = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

            return Article(
                url=url,
                source='vnexpress',
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
    crawler = VNExpressCrawler(category='thoi-su')
    articles = crawler.run()
    print(f"Crawled {len(articles)} articles")
    if articles:
        print(articles[0])