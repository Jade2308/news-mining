"""Simple inference script for PhoBERT clickbait classifier"""
import logging
import sys
from pathlib import Path

# Ensure project root is in Python path when running as script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import MODEL_DIR
from models.phobert_classifier import PhoBERTClickbaitClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test PhoBERT model on sample Vietnamese titles."""
    
    model_path = str(MODEL_DIR)
    
    # Check if model exists
    if not Path(model_path).exists():
        logger.error(f"❌ Model not found at {model_path}")
        logger.info("Please train the model first:")
        logger.info("  python src/models/train_clickbait.py")
        return
    
    # Load model
    logger.info(f"🤖 Loading model from {model_path}")
    model = PhoBERTClickbaitClassifier(model_name=model_path)
    
    # Sample titles for testing
    test_titles = [
        # Non-clickbait (news titles)
        "Quốc hội bước vào tuần làm việc cuối cùng của kỳ họp dài kỷ lục",
        "Sân bay Vinh đóng cửa 6 tháng để nâng cấp",
        "5 người thoát nạn khi ôtô bị lũ cuốn",
        "Quy hoạch 9 khu chức năng phía đông TP HCM",
        "Bộ trưởng trao quyết định thành lập Cơ quan Ủy ban Trung ương MTTQ Việt Nam",
        
        # Potential clickbait titles
        "KHÔNG THỂ TIN ĐƯỢC! Cái gì xảy ra tiếp theo sẽ SHOCK bạn",
        "BÍ MẬT CỦA SÔNG HÀN MÀ KHÔNG MỘT AI BIẾT!",
        "XỬ LÝ NGƯỜI NƯỚC NGOÀI LỪA ĐẢO: Điều gì xảy ra sẽ làm bạn GIẬT MÌNH",
        "HÃY XEM VIDEO NÀY TRƯỚC KHI NÓ BỊ XÓA",
        "CÁCH TIẾP THỊ GỬI BẠNH CHỈ SAU 1 NGÀY",
    ]
    
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTING PHOBERT CLICKBAIT CLASSIFIER")
    logger.info("="*80 + "\n")
    
    for i, title in enumerate(test_titles, 1):
        label, probs = model.predict(title, return_probs=True)
        label_name = "CLICKBAIT" if label == 1 else "NON-CLICKBAIT"
        
        logger.info(f"[{i:2d}] {label_name}")
        logger.info(f"      Title: {title[:70]}")
        if len(title) > 70:
            logger.info(f"             {title[70:]}")
        logger.info(f"      Confidence: {probs[label]:.2%}")
        logger.info(f"      Probs: Non-clickbait={probs[0]:.2%}, Clickbait={probs[1]:.2%}")
        logger.info("")
    
    logger.info("="*80)
    logger.info("✅ Testing completed!")
    logger.info("="*80)


if __name__ == '__main__':
    main()
