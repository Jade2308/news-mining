"""Integration of PhoBERT clickbait detection with database operations"""
import logging
import sys
from typing import Tuple, Optional
from pathlib import Path

# Fix imports to use the new package structure
from ai_news.config import MODEL_DIR
from ai_news.models.phobert_classifier import PhoBERTClickbaitClassifier

logger = logging.getLogger(__name__)

# Cache the model to avoid reloading
_CLICKBAIT_MODEL = None
_MODEL_PATH = str(MODEL_DIR)


def get_clickbait_model():
    """Lazy load PhoBERT model (singleton pattern).
    
    Returns:
        PhoBERTClickbaitClassifier or None if model not available
    """
    global _CLICKBAIT_MODEL
    
    if _CLICKBAIT_MODEL is not None:
        return _CLICKBAIT_MODEL
    
    # Try to load model
    try:
        # Check if model exists
        if not Path(_MODEL_PATH).exists():
            logger.warning(f"❌ Model not found at {_MODEL_PATH}")
            logger.info("   Please train the model first using:")
            logger.info("   python -m ai_news.models.train_clickbait")
            return None
        
        logger.info(f"🤖 Loading PhoBERT model from {_MODEL_PATH}")
        _CLICKBAIT_MODEL = PhoBERTClickbaitClassifier(model_name=_MODEL_PATH)
        logger.info("✅ PhoBERT model loaded successfully")
        return _CLICKBAIT_MODEL
        
    except ImportError as e:
        logger.error(f"❌ Could not import PhoBERT: {e}")
        logger.info("   Make sure transformers and torch are installed:")
        logger.info("   pip install -r requirements.txt")
        return None
    except Exception as e:
        logger.error(f"❌ Error loading PhoBERT model: {e}")
        return None


def detect_clickbait(
    title: str,
    summary: Optional[str] = None,
    use_summary: bool = False
) -> Tuple[int, float, str]:
    """Detect if article is clickbait using PhoBERT.
    
    Args:
        title: Article title (required)
        summary: Article summary/lead paragraph (optional)
        use_summary: If True, use both title and summary for better prediction
        
    Returns:
        Tuple of (label, confidence, label_name):
        - label: 1 for clickbait, 0 for non-clickbait
        - confidence: Confidence score (0.0 to 1.0)
        - label_name: 'clickbait' or 'non-clickbait'
    """
    model = get_clickbait_model()
    
    if model is None:
        # Default to non-clickbait if model not available
        logger.debug("PhoBERT model not available, defaulting to non-clickbait")
        return 0, 0.5, 'non-clickbait'
    
    try:
        # Prepare text for prediction
        if use_summary and summary:
            # Combine title and summary with separator
            text = f"{title} {summary}"
        else:
            text = title
        
        # Get prediction
        label, confidence = model.predict(text)
        label_name = 'clickbait' if label == 1 else 'non-clickbait'
        
        return label, confidence, label_name
        
    except Exception as e:
        logger.error(f"Error in clickbait detection: {e}")
        return 0, 0.5, 'non-clickbait'


def detect_clickbait_batch(
    articles: list,
    title_key: str = 'title',
    summary_key: Optional[str] = 'summary',
    use_summary: bool = False
) -> list:
    """Detect clickbait for multiple articles.
    
    Args:
        articles: List of article dicts
        title_key: Key for title field in article dict
        summary_key: Key for summary field in article dict
        use_summary: If True, use both title and summary
        
    Returns:
        List of dicts with original article + detection results:
        {
            'title': str,
            'summary': str,
            'clickbait_label': int,
            'clickbait_confidence': float,
            'clickbait_label_name': str
        }
    """
    results = []
    
    for i, article in enumerate(articles):
        try:
            title = str(article.get(title_key, ''))
            summary = str(article.get(summary_key, '')) if summary_key else None
            
            if not title:
                logger.warning(f"Article {i} has no title, skipping")
                continue
            
            label, confidence, label_name = detect_clickbait(
                title, summary, use_summary
            )
            
            result = {
                **article,
                'clickbait_label': label,
                'clickbait_confidence': confidence,
                'clickbait_label_name': label_name
            }
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing article {i}: {e}")
            continue
    
    return results


def filter_clickbait(articles: list, keep_clickbait: bool = False) -> list:
    """Filter articles by clickbait status.
    
    Args:
        articles: List of articles with clickbait detection
        keep_clickbait: If True, keep only clickbait; if False, remove clickbait
        
    Returns:
        Filtered list of articles
    """
    filtered = []
    
    for article in articles:
        label = article.get('clickbait_label', 0)
        
        if keep_clickbait:
            # Keep clickbait articles
            if label == 1:
                filtered.append(article)
        else:
            # Keep non-clickbait articles
            if label == 0:
                filtered.append(article)
    
    return filtered


# Example usage in database operations
def insert_article_with_clickbait_detection(
    data: dict,
    detect_clickbait_flag: bool = True,
    db_path: str = None
) -> Tuple[str, Optional[dict]]:
    """Insert article and optionally detect clickbait.
    
    This is a wrapper around insert_article that adds clickbait detection.
    Should be used instead of raw insert_article when clickbait detection is enabled.
    
    Args:
        data: Article data dict
        detect_clickbait_flag: Whether to run clickbait detection
        db_path: Path to database
        
    Returns:
        Tuple of (insert_status, clickbait_result):
        - insert_status: 'inserted', 'dup_url', 'dup_fp'
        - clickbait_result: Dict with detection results or None
    """
    from ai_news.database.db import insert_article
    
    clickbait_result = None
    
    # Run clickbait detection if enabled
    if detect_clickbait_flag:
        title = data.get('title', '')
        summary = data.get('summary', '')
        
        label, confidence, label_name = detect_clickbait(title, summary, use_summary=True)
        
        clickbait_result = {
            'label': label,
            'confidence': confidence,
            'label_name': label_name
        }
        
        # Log if clickbait detected
        if label == 1:
            logger.warning(
                f"⚠️  CLICKBAIT DETECTED: {title[:60]}... (confidence: {confidence:.2%})"
            )
        
        # Add to article data for optional storage
        data['clickbait_label'] = label
        data['clickbait_confidence'] = confidence
    
    # Insert into database
    insert_status = insert_article(data, db_path=db_path) if db_path else insert_article(data)
    
    return insert_status, clickbait_result


# Test function
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test detect_clickbait
    test_titles = [
        "Quốc hội bước vào tuần làm việc cuối cùng của kỳ họp dài kỷ lục",
        "KHÔNG THỂ TIN ĐƯỢC! Cái gì xảy ra tiếp theo sẽ SHOCK bạn",
        "5 người thoát nạn khi ôtô bị lũ cuốn",
        "BÍ MẬT CỦA SÔNG HÀN MÀ KHÔNG MỘT AI BIẾT!"
    ]
    
    logger.info("🧪 Testing PhoBERT clickbait detection")
    logger.info("="*60)
    
    for title in test_titles:
        label, confidence, label_name = detect_clickbait(title)
        logger.info(f"Title: {title[:50]}...")
        logger.info(f"  → {label_name.upper()} (confidence: {confidence:.2%})")
        logger.info("")
