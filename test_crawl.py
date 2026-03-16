# test_crawl.py
from crawlers.vnexpress_crawler import VNExpressCrawler
from database.db import insert_article

crawler = VNExpressCrawler(category='kinh-doanh')
articles = crawler.run()

# Lưu vào DB
for article in articles:
    insert_article(article)

print(f'Inserted {len(articles)} articles')