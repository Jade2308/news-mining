import os
import logging
from typing import List, Dict, Any, Tuple

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    def __init__(self, embedding_model="paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize the BERTopic model specifically tuned for Vietnamese text.
        """
        try:
            logger.info(f"Loading embedding model: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)
            
            # Dimensionality reduction
            # Thêm n_jobs=1 để tránh lỗi treo (hang) process khi chạy UMAP trên điều hành Windows
            self.umap_model = UMAP(
                n_neighbors=15, 
                n_components=5, 
                min_dist=0.0, 
                metric='cosine', 
                random_state=42,
                n_jobs=1
            )
            
            # Clustering model: Quá trình test cho thấy KMeans ép chùm quá to. 
            # Ta quay lại HDBSCAN và khai báo cực chặt: Chỉ gom nếu có 5-10 bài cực giống nhau
            from hdbscan import HDBSCAN
            self.hdbscan_model = HDBSCAN(
                min_cluster_size=5, 
                min_samples=2,
                metric='euclidean', 
                cluster_selection_method='eom', 
                prediction_data=True
            )
            
            # 1. (Đã gỡ bỏ underthesea do dính lỗi môi trường trên Windows)
            # Chúng ta sẽ sử dụng Tokenizer mặc định kết hợp ngram_range=(1, 3) 
            # để tự động bắt được các cụm từ (ví dụ "công an", "học sinh") mà không cần underthesea.

            # 2. Loại bỏ các "stop words" (từ nối vô nghĩa tiếng Việt) để kết quả tập trung vào từ thực sự có ý nghĩa
            vn_stopwords = [
                "của", "bị", "và", "tại", "là", "trong", "có", "cho", "với", "đã", "nhưng", "từ", "một", "những", 
                "người", "để", "này", "khi", "đến", "các", "như", "về", "được", "sẽ", "sự", "không", "thì", "cũng", 
                "nhiều", "hơn", "sau", "đang", "lại", "đó", "phải", "năm", "ngày", "làm", "nay", "vào", "ra", "đồng"
            ]
            
            self.vectorizer_model = CountVectorizer(
                stop_words=vn_stopwords,
                ngram_range=(1, 3) # Mở rộng n-gram để lấy được các cụm dài có nghĩa
            )
            
            # 3. Sử dụng mô hình KeyBERTInspired giúp chắt lọc từ khóa sát nghĩa với nội dung cả cụm bài nhất
            from bertopic.representation import KeyBERTInspired
            self.representation_model = KeyBERTInspired()
            
            self.topic_model = BERTopic(
                embedding_model=self.embedding_model,
                umap_model=self.umap_model,
                hdbscan_model=self.hdbscan_model,
                vectorizer_model=self.vectorizer_model,
                representation_model=self.representation_model,
                language="multilingual",
                verbose=True
            )
            self.is_fitted = False
            logger.info("TopicAnalyzer initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing TopicAnalyzer: {e}")
            raise

    def extract_hot_topics(self, docs: List[str]) -> Tuple[List[int], Any]:
        """
        Extract topics from a list of documents.
        Returns:
            topics: List of topic integer IDs assigned to each document
            probs: Probabilities of assignments (if available)
        """
        if not docs:
            logger.warning("Empty document list provided.")
            return [], None
            
        logger.info(f"Extracting topics from {len(docs)} documents...")
        topics, probs = self.topic_model.fit_transform(docs)
        self.is_fitted = True
        return topics, probs

    def get_topic_info(self) -> Any:
        """Get information about the extracted topics as a DataFrame."""
        if not self.is_fitted:
            return None
        return self.topic_model.get_topic_info()

    def get_top_topics(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get the most frequent topics excluding the outlier topic (-1)."""
        if not self.is_fitted:
            logger.warning("Topic model has not been fitted yet.")
            return []
            
        topic_info = self.topic_model.get_topic_info()
        # Filter out outlier topic (-1)
        valid_topics = topic_info[topic_info['Topic'] != -1]
        
        results = []
        for _, row in valid_topics.head(top_n).iterrows():
            topic_id = row['Topic']
            count = row['Count']
            
            # Get the top keywords for this topic
            keywords = self.topic_model.get_topic(topic_id)
            if keywords:
                # format of keywords is list of tuples: [('word', score), ...]
                top_words = [kw[0] for kw in keywords[:5]]
                
                # Phương pháp thay thế API: Lấy bài viết mang tính đại diện (điển hình) nhất cho cụm
                # Câu đầu tiên của bài viết đó chính là tiêu đề (do chúng ta ghép title. summary)
                rep_docs = self.topic_model.get_representative_docs(topic_id)
                rep_title = rep_docs[0].replace('\n', ' ').split('.', 1)[0].strip() if rep_docs else ""
                
                results.append({
                    'topic_id': topic_id,
                    'count': count,
                    'keywords': top_words,
                    'rep_title': rep_title,
                    'name': row.get('Name', '')
                })
                
        return results
