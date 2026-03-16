import re
from datetime import datetime, timedelta

def normalize_text(text):
    """Chuẩn hóa text: bỏ khoảng trắng thừa"""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_relative_time(time_str):
    """
    Parse thời gian tương đối như:
    - '2 giờ trước'
    - '30 phút trước'
    - 'hôm qua'
    Nếu không parse được -> trả về datetime.now()
    """
    if not time_str:
        return datetime.now()

    time_str = time_str.lower().strip()
    now = datetime.now()

    try:
        if 'giờ trước' in time_str:
            m = re.search(r'(\d+)', time_str)
            if m:
                return now - timedelta(hours=int(m.group(1)))

        if 'phút trước' in time_str:
            m = re.search(r'(\d+)', time_str)
            if m:
                return now - timedelta(minutes=int(m.group(1)))

        if 'hôm qua' in time_str:
            return now - timedelta(days=1)

    except Exception:
        pass

    return now