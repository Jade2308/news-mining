# crawlers/utils.py
import re
from datetime import datetime, timedelta

def normalize_text(text):
    """Chuẩn hóa text"""
    if not text:
        return ''
    # Bỏ khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_relative_time(time_str):
    """Parse thời gian dạng 'N giờ trước' thành datetime"""
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    # Ví dụ: "2 giờ trước", "30 phút trước", "hôm qua"
    if 'giờ trước' in time_str:
        hours = int(re.search(r'(\d+)', time_str).group(1))
        return now - timedelta(hours=hours)
    elif 'phút trước' in time_str:
        minutes = int(re.search(r'(\d+)', time_str).group(1))
        return now - timedelta(minutes=minutes)
    elif 'hôm qua' in time_str:
        return now - timedelta(days=1)
    else:
        return now

if __name__ == '__main__':
    print(parse_relative_time('2 giờ trước'))