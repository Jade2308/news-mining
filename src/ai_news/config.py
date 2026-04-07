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
