"""
config.py
Global configuration for the project with centralized path management.
"""

import os
from pathlib import Path

# --- Path Configuration ---
# PACKAGE_ROOT is 'src/ai_news'
PACKAGE_ROOT = Path(__file__).resolve().parent
# PROJECT_ROOT is the top-level directory
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

# Data directory for CSVs, JSONs and Database
DATA_DIR = PROJECT_ROOT / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Artifacts directory for trained models and evaluation results
ARTIFACTS_DIR = PROJECT_ROOT / 'artifacts'
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration
DB_PATH = str(DATA_DIR / 'news.db')

# ML Model configuration
MODEL_DIR = ARTIFACTS_DIR / 'models' / 'phobert_clickbait'
EVALUATION_DIR = ARTIFACTS_DIR / 'evaluation'

# Default dataset path
DATASET_CSV = str(DATA_DIR / 'clickbait_dataset_vietnamese.csv')
CATEGORIES_JSON = str(DATA_DIR / 'discovered_categories.json')

# --- Crawler Sources & Categories ---
SOURCES = {
    'vnexpress': {
        'name': 'VNExpress',
        'base_url': 'https://vnexpress.net',
        'categories': {
            'thoi-su': 'thời sự',
            'the-gioi': 'thế giới',
            'khoa-hoc-cong-nghe': 'khoa học công nghệ',
            'kinh-doanh': 'kinh doanh',
            'suc-khoe': 'sức khỏe',
            'the-thao': 'thể thao',
            'giai-tri': 'giải trí',
            'phap-luat': 'pháp luật',
            'giao-duc': 'giáo dục',
            'doi-song': 'đời sống',
            'xe': 'xe',
            'du-lich': 'du lịch',
        }
    },
    'tuoitre': {
        'name': 'Tuổi Trẻ',
        'base_url': 'https://tuoitre.vn',
        'categories': {
            'thoi-su': 'thời sự',
            'the-gioi': 'thế giới',
            'phap-luat': 'pháp luật',
            'cong-nghe': 'công nghệ',
            'xe': 'xe',
            'du-lich': 'du lịch',
            'van-hoa': 'văn hóa',
            'giai-tri': 'giải trí',
            'the-thao': 'thể thao',
            'giao-duc': 'giáo dục',
            'suc-khoe': 'sức khỏe',
        }
    },
    'vietnamnet': {
        'name': 'VietnamNet',
        'base_url': 'https://vietnamnet.vn',
        'categories': {
            'chinh-tri': 'chính trị',
            'thoi-su': 'thời sự',
            'giao-duc': 'giáo dục',
            'the-gioi': 'thế giới',
            'the-thao': 'thể thao',
            'doi-song': 'đời sống',
            'suc-khoe': 'sức khỏe',
            'cong-nghe': 'công nghệ',
            'phap-luat': 'pháp luật',
            'du-lich': 'du lịch',
        }
    }
}
