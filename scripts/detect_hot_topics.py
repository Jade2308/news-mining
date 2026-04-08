import os
import sys
import logging
import argparse
import requests
from dotenv import load_dotenv

# Thêm đường dẫn thư mục gốc vào sys.path để import được database/ và processing/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_articles_by_timerange, save_hot_topics
from processing.topic_bertopic import TopicAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def generate_topic_name_with_gemma(keywords, titles, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-3-27b-it:generateContent?key={api_key}"
    prompt = (
        "Bạn là một biên tập viên báo chí. "
        "Hãy đọc danh sách từ khóa và tiêu đề của một cụm các bài báo dưới đây, và nghĩ ra MỘT CÂU tiêu đề CHỈNH CHU, NGẮN GỌN (tối đa 10 chữ) để đặt tên cho dải chủ đề này (ví dụ: 'Chiến sự Mỹ và Iran' thay vì 'mỹ, iran, chiến tranh').\n\n"
        f"Từ khóa: {', '.join(keywords)}\n"
        f"Tiêu đề nhóm bài:\n" + "\n".join([f"- {t}" for t in titles]) + "\n\n"
        "Tên chủ đề ngắn gọn:"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"Gemma API Error [{resp.status_code}]: {resp.text}")
            return None
            
        data = resp.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '').replace('*', '')
        else:
            logger.warning(f"Phản hồi không mong muốn từ Gemma: {data}")
    except Exception as e:
        logger.warning(f"Lỗi khi gọi Gemma API: {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Detect hot topics from recent news using BERTopic.")
    parser.add_argument('--hours', type=int, default=24, help="Number of hours to look back for articles.")
    parser.add_argument('--top_n', type=int, default=10, help="Number of top topics to display.")
    args = parser.parse_args()
    
    logger.info(f"Fetching articles from the last {args.hours} hours...")
    articles = get_articles_by_timerange(hours=args.hours)
    
    if not articles:
        logger.info("No articles found in the specified time frame.")
        return
        
    logger.info(f"Found {len(articles)} articles. Preparing data...")
    
    # Chuẩn bị văn bản đầu vào: kết hợp title và summary
    docs = []
    article_mapping = [] # dùng để map kết quả về lại bài báo gốc
    
    for article in articles:
        title = (article.get('title') or '').strip()
        summary = (article.get('summary') or '').strip()
        text = f"{title}. {summary}".strip()
        
        if text:
            docs.append(text)
            article_mapping.append(article)
            
    if len(docs) < 15:
        logger.warning(f"Not enough documents for HDBSCAN clustering (found {len(docs)}, usually needs >=15). Try increasing --hours.")
        return
        
    logger.info("Initializing TopicAnalyzer (this may download models if running for the first time)...")
    analyzer = TopicAnalyzer()
    
    logger.info("Running BERTopic extraction (this may take a minute computing embeddings...)...")
    topics, _ = analyzer.extract_hot_topics(docs)
    
    hot_topics = analyzer.get_top_topics(top_n=args.top_n)
    topics_to_save = []
    
    print("\n" + "="*60)
    print(f"🔥 HOT TOPICS IN THE LAST {args.hours} HOURS 🔥")
    print("="*60)
    
    if not hot_topics:
        print("\nKhông tìm thấy chủ đề nào nổi bật. Có thể các bài quá rời rạc hoặc toàn outlier.")
        return
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        logger.info("Đã tìm thấy API_KEY, đang nhờ AI tóm tắt thành tên chủ đề siêu đẹp...")
        
    for i, ht in enumerate(hot_topics, 1):
        # Lấy thẳng những bài báo cốt lõi của cụm
        rep_docs = analyzer.topic_model.get_representative_docs(ht['topic_id'])
        
        # ĐẶT TÊN CHỦ ĐỀ CHẮC CHẮN VÀ ỔN ĐỊNH NHẤT
        # Thay vì dựa vào AI nhỏ thường ảo giác, ta nối 3 Keyword Lõi thành Tag (Đậm chất báo điện tử)
        topic_name = " | ".join(ht['keywords'][:3]).upper()
        
        titles_for_llm = [text.split('.', 1)[0] for text in rep_docs[:5]] if rep_docs else []
        
        if api_key and rep_docs:
            logger.info("Đang gọi Google Gemma-3-27B-IT (Mô hình miễn phí KHỦNG nhất)...")
            ai_name = generate_topic_name_with_gemma(ht['keywords'], titles_for_llm, api_key)
            if ai_name:
                topic_name = ai_name.replace('"', '').replace('*', '').upper()
                
        # Get actual article_ids forming this cluster
        article_ids = []
        for idx, t_id in enumerate(topics):
            if t_id == ht['topic_id']:
                article_ids.append(article_mapping[idx]['article_id'])
                
        topics_to_save.append({
            'topic_name': topic_name,
            'keywords': ', '.join(ht['keywords']),
            'article_count': ht['count'],
            'article_ids': article_ids
        })
                
        print(f"\n[{i}] 📌 CHỦ ĐỀ: {topic_name} (ID: {ht['topic_id']} | SỐ BÀI: {ht['count']})")
        print(f"    ⭐ TỪ KHÓA LÕI: {', '.join(ht['keywords'][:5])}")
        print(f"    📰 BÀI MẪU (Chuẩn xác nhất):")
        
        if rep_docs:
            for rep_text in rep_docs[:5]:
                try:
                    idx = docs.index(rep_text)
                    title = article_mapping[idx].get('title')
                    source = article_mapping[idx].get('source')
                    print(f"      - {title} ({source})")
                except ValueError:
                    title = rep_text.split('.', 1)[0]
                    print(f"      - {title}")
            
    print("\n" + "="*60 + "\n")
    
    if topics_to_save:
        save_hot_topics(topics_to_save, args.hours)

if __name__ == "__main__":
    main()
