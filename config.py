# config.py

# Cấu hình nguồn tin
SOURCES = {
    'vnexpress': {
        'base_url': 'https://vnexpress.net',
        'name': 'VNExpress',
        'categories': {
            'kinh-doanh': 'Kinh tế',
            'khoa-hoc': 'Công nghệ',
            'the-thao': 'Thể thao',
            'giai-tri': 'Giải trí',
        }
    },
    'tuoitre': {
        'base_url': 'https://tuoitre.vn',
        'name': 'Tuổi Trẻ Online',
        'categories': {
            'thoi-su': 'Thời sự',
            'cong-nghe': 'Công nghệ',
            'the-thao': 'Thể thao',
            'giao-duc': 'Giáo dục',
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
DB_PATH = 'news.db'