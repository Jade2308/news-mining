import logging
from crawlers._vnexpress import VNExpressCrawler
from database.models import init_db
from database.engine import insert_article

def main():
    logging.basicConfig(level=logging.INFO)
    init_db()  # ✅ tạo bảng articles nếu chưa có
    
    crawler = VNExpressCrawler(category='kinh-doanh')
    articles = crawler.run()

    for article in articles:
        insert_article(article)

    print(f'Inserted {len(articles)} articles')

if __name__ == "__main__":
    main()