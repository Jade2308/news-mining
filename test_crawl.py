from crawlers.vnexpress_crawler import VNExpressCrawler
from database.schema import init_db
from database.db import insert_article

init_db()  # ✅ tạo bảng articles nếu chưa có

crawler = VNExpressCrawler(category='kinh-doanh')
articles = crawler.run()

for article in articles:
    insert_article(article)

print(f'Inserted {len(articles)} articles')