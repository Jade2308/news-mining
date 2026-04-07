"""
database/__init__.py
Export main database functions
"""

from ai_news.database. import init_db
from ai_news.database. import (
    add_prediction,
    add_batch_predictions,
    get_unpredicted_articles,
    get_prediction_stats,
    get_sample_predictions
)

__all__ = [
    'init_db',
    'add_prediction',
    'add_batch_predictions',
    'get_unpredicted_articles',
    'get_prediction_stats',
    'get_sample_predictions'
]
