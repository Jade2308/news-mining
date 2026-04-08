import sys
import os
import subprocess
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PYTHON_CMD = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_script(*args):
    """Hàm phụ trợ để gọi subprocess các script python."""
    try:
        subprocess.run([PYTHON_CMD] + list(args), check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi chạy {' '.join(args)}: {e}")

def hourly_job():
    now = datetime.now()
    logger.info(f"========== Bắt đầu lịch trình lúc {now.strftime('%Y-%m-%d %H:%M:%S')} ==========")
    
    crawl_script = os.path.join(BASE_DIR, 'crawl_hourly.py')
    detect_script = os.path.join(BASE_DIR, 'detect_hot_topics.py')
    
    # 1. Luôn chạy Crawl hằng giờ
    logger.info(f"[{now.strftime('%H:%M')}] -> Đang chạy Crawl dữ liệu...")
    run_script(crawl_script)
    
    # 2. Luôn chạy phân tích chủ đề 1h
    logger.info(f"[{now.strftime('%H:%M')}] -> Phân tích chủ đề 1 giờ gần nhất...")
    run_script(detect_script, '--hours', '1')
    
    # 3. Phân tích 6h vào các mốc: 00h, 06h, 12h, 18h
    if now.hour in (0, 6, 12, 18):
        logger.info(f"[{now.strftime('%H:%M')}] -> Phân tích chủ đề 6 giờ (Mốc 00, 06, 12, 18)...")
        run_script(detect_script, '--hours', '6')
        
    # 4. Phân tích 24h và 1 Tuần vào mốc 00h
    if now.hour == 0:
        logger.info(f"[{now.strftime('%H:%M')}] -> Phân tích chủ đề 24h (Cuối ngày)...")
        run_script(detect_script, '--hours', '24')
        
        logger.info(f"[{now.strftime('%H:%M')}] -> Phân tích chủ đề 1 tuần (168h)...")
        run_script(detect_script, '--hours', '168')
        
    logger.info("========== Hoàn tất lịch trình ==========\n")

def start_scheduler():
    scheduler = BlockingScheduler()
    
    # Đặt lịch chạy TỰ ĐỘNG CHÍNH XÁC VÀO TỪNG ĐẦU GIỜ (phút 00)
    scheduler.add_job(hourly_job, 'cron', minute=0)
    
    logger.info("🚀 Vận hành Bộ lập lịch (Scheduler).")
    logger.info("Hệ thống sẽ tự động kích hoạt vào phút 00 mỗi giờ: 13:00, 14:00,...")
    logger.info("- Mỗi giờ: Chạy crawl và phân tích mốc 1h")
    logger.info("- Mỗi 6 giờ (00h, 6h, 12h, 18h): Chạy thêm mốc 6h")
    logger.info("- Mỗi 00h đêm: Chạy thêm mốc 24h và 168h (1 tuần)")
    logger.info("Bấm Ctrl+C để thoát khỏi trình tự động.")
    
    # Nếu muốn khi vừa bật file này lên nó chạy thử 1 lần ngay lập tức thì bỏ ghi chú dòng dưới
    # hourly_job() 

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Đã tắt hệ thống Scheduler.")

if __name__ == "__main__":
    start_scheduler()
