"""
config.py
Global configuration for the project
"""

import os

# Database configuration
DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'news.db'
)
