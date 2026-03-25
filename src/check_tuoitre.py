import logging
from pprint import pprint

from crawlers._tuoitre import TuoitreCrawler


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s"
    )
    logger = logging.getLogger("test_crawl_tuoitre")

    category = "thoi-su"
    limit = 10
    crawler = TuoitreCrawler(category=category)

    articles = crawler.run()
    if limit and len(articles) > limit:
        articles = articles[:limit]

    if not articles:
        print("\n⚠️ Không crawl được bài nào.\n")
        return

    print(f"\n✅ Total parsed articles: {len(articles)}\n")

    for i, article in enumerate(articles[:5], 1):
        print(f"--- Article #{i} ---")
        if isinstance(article, dict):
            pprint({
                "title": article.get("title"),
                "url": article.get("url"),
                "published_at": article.get("published_at"),
            })
        else:
            pprint({
                "title": getattr(article, "title", None),
                "url": getattr(article, "url", None),
                "published_at": getattr(article, "published_at", None),
            })
        print()

    logger.info("Test crawl TuoiTre hoàn tất.")


if __name__ == "__main__":
    main()