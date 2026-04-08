import subprocess
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 1h, 6h, 12h, 24h, 1 tuần (168h)
    timeframes = [1, 6, 12, 24, 168]
    python_executable = sys.executable
    
    script_path = os.path.join(os.path.dirname(__file__), 'detect_hot_topics.py')
    
    for tf in timeframes:
        logger.info(f"========== Bắt đầu chạy phát hiện chủ đề cho khoảng thời gian: {tf} giờ ==========")
        try:
            # Dùng subprocess để chạy script detect_hot_topics.py
            subprocess.run(
                [python_executable, script_path, '--hours', str(tf)],
                check=True
            )
            logger.info(f"✅ Đã chạy thành công cho {tf} giờ.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Lỗi khi chạy cho {tf} giờ: {e}\n")
            
if __name__ == '__main__':
    main()
