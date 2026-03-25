# config.py

# Cấu hình nguồn tin
SOURCES = {
    'vnexpress': {
        'base_url': 'https://vnexpress.net',
        'name': 'VNExpress',
        'categories': {
            'thoi-su': 'Thời sự',
            'kinh-doanh': 'Kinh doanh',
            'cong-nghe': 'Khoa học công nghệ',
            'giai-tri': 'Giải trí',
            'the-thao': 'Thể thao',
            'suc-khoe': 'Sức khỏe',
        }
    },
    'tuoitre': {
        'base_url': 'https://tuoitre.vn',
        'name': 'Tuổi Trẻ Online',
        'categories': {
            'thoi-su': 'Thời sự',
            'kinh-doanh': 'Kinh doanh',
            'cong-nghe': 'Công nghệ',
            'giai-tri': 'Giải trí',
            'the-thao': 'Thể thao',
            'suc-khoe': 'Sức khỏe',
        }
    }
}

# Cấu hình scheduler
CRAWL_INTERVAL_MINUTES = 15  # Crawl mỗi 15 phút
CLICKBAIT_INTERVAL_MINUTES = 30  # Clickbait mỗi 30 phút
TOPIC_INTERVAL_HOURS = 6  # Topic batch mỗi 6 giờ

# Cấu hình topic modeling
N_TOPICS = 8  # Số chủ đề
TOPIC_METHOD = 'lda'  # 'lda' hoặc 'bertopic'

# Cấu hình clickbait
CLICKBAIT_SAMPLE_SIZE = 300  # Bao nhiêu bài gán nhãn thủ công

# Cơ sở dữ liệu
DB_PATH = 'data/news.db'