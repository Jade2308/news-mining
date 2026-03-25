import re
import time
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler
from crawlers.helpers import normalize_text, parse_time
from core.shared_types import Article
from core.cleaner import extract_text_from_html, clean_text

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))


_LISTING_BLACKLIST = [
    '/video', '/podcast', '/infographic', '/multimedia',
    '/tag/', '/tim-kiem.htm', '/rss.htm',
]

# Article URLs on Tuổi Trẻ usually end with a long numeric ID before .htm,
# e.g. "ten-bai-2026031813171468.htm". Avoid section pages like "...-360.htm".
_ARTICLE_URL_RE = re.compile(r'-\d{7,}\.htm$')


class TuoitreCrawler(BaseCrawler):
    def __init__(self, category='thoi-su'):
        super().__init__('tuoitre', category)
        self.base_url = 'https://tuoitre.vn'

        # Mapping category chuẩn hóa -> URL thực tế của Tuổi Trẻ
        self.category_urls = {
            'thoi-su': 'https://tuoitre.vn/thoi-su.htm',
            'kinh-doanh': 'https://tuoitre.vn/kinh-doanh.htm',
            'cong-nghe': 'https://tuoitre.vn/cong-nghe.htm',
            'giai-tri': 'https://tuoitre.vn/giai-tri.htm',
            'the-thao': 'https://tuoitre.vn/the-thao.htm',
            'suc-khoe': 'https://tuoitre.vn/suc-khoe.htm',
        }

    def fetch_listing(self):
        """Lấy danh sách URL bài từ trang chuyên mục Tuổi Trẻ."""
        url = self.category_urls.get(self.category, self.base_url)
        logger.info(f"Fetching listing from {url}")

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, 'html.parser')

            candidate_links = []
            selectors = [
                'h3 a[href]',
                'h2 a[href]',
                'article a[href]',
                'a.box-category-link-with-avatar[href]',
                'a[href*=".htm"]',
            ]
            for sel in selectors:
                candidate_links.extend(soup.select(sel))

            urls = []
            seen = set()

            blacklist = _LISTING_BLACKLIST

            for a in candidate_links:
                href = a.get('href', '').strip()
                if not href:
                    continue

                full_url = urljoin(self.base_url, href)

                if not full_url.startswith(self.base_url):
                    continue
                if '.htm' not in full_url:
                    continue
                if any(x in full_url for x in blacklist):
                    continue
                # Only accept real article URLs (end with -<digits>.htm)
                if not _ARTICLE_URL_RE.search(full_url):
                    continue
                if full_url in seen:
                    continue

                seen.add(full_url)
                urls.append(full_url)

                if len(urls) >= 50:
                    break

            logger.info(f"Found {len(urls)} article urls")
            return urls

        except Exception as e:
            logger.error(f"Error fetching listing: {e}", exc_info=True)
            return []

    def parse_article(self, url):
        """Parse 1 bài từ Tuổi Trẻ và trả về Article theo schema chuẩn."""
        time.sleep(0.5)

        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            html = r.text
            soup = BeautifulSoup(r.content, 'html.parser')

            # --- Title (required) ---
            title_elem = soup.select_one('h1.detail-title, h1.article-title, h1')
            title = normalize_text(title_elem.get_text()) if title_elem else ''
            if not title:
                logger.warning(f"No title found for {url}, skipping")
                return None

            # --- Summary / sapo ---
            summary_elem = soup.select_one(
                'h2.detail-sapo, p.detail-sapo, p.sapo, p.article__summary'
            )
            summary = normalize_text(summary_elem.get_text()) if summary_elem else ''

            # --- Author ---
            author_elem = soup.select_one(
                'div.author-info strong, p.author-name, span.author'
            )
            author = normalize_text(author_elem.get_text()) if author_elem else None

            # --- Tags ---
            tag_elems = soup.select('ul.tags a, div.tags a, a.tag-item')
            tags = [normalize_text(t.get_text()) for t in tag_elems if t.get_text(strip=True)]

            # --- Content ---
            content_elem = soup.select_one(
                'div.detail-content, div#main-detail-body, div.article__content'
            )
            content_html_raw = str(content_elem) if content_elem else ''
            content_text = extract_text_from_html(
                content_html_raw or html,
                content_selector='div.detail-content, div#main-detail-body',
            )
            content_text = clean_text(content_text)

            # --- Published time ---
            published_at = None

            meta_time_elem = soup.select_one(
                'meta[property="article:published_time"], '
                'meta[name="pubdate"], '
                'meta[name="publishdate"]'
            )
            if meta_time_elem and meta_time_elem.get('content'):
                published_at = parse_time(meta_time_elem.get('content'))

            if not published_at:
                time_elem = soup.select_one(
                    'div.date-time, div.detail-time, span.date-time, '
                    'span.article__time, time[datetime]'
                )
                if time_elem:
                    # Prefer machine-readable datetime attribute
                    dt_attr = time_elem.get('datetime')
                    if dt_attr:
                        published_at = parse_time(dt_attr)
                    else:
                        published_at = parse_time(normalize_text(time_elem.get_text()))

            # --- Crawled at ---
            crawled_at = datetime.now(_VN_TZ).strftime('%Y-%m-%d %H:%M:%S')

            return Article(
                url=url,
                source='tuoitre',
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
            logger.error(f"Error parsing {url}: {e}", exc_info=True)
            return None


if __name__ == '__main__':
    crawler = TuoitreCrawler(category='thoi-su')
    articles = crawler.run()
    print(f"Crawled {len(articles)} articles")
    if articles:
        print(articles[0]['title'])