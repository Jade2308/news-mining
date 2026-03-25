#!/usr/bin/env python3
"""
scripts/init_db.py – Khởi tạo cơ sở dữ liệu SQLite cho news-mining.

Cách dùng:
    python scripts/init_db.py
    python scripts/init_db.py --db-path /path/to/custom.db
"""
import argparse
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.settings import DB_PATH
from database.models import init_db


def main():
    parser = argparse.ArgumentParser(
        description='Khởi tạo SQLite database cho news-mining.'
    )
    parser.add_argument(
        '--db-path',
        default=DB_PATH,
        help=f'Đường dẫn tới file DB (mặc định: {DB_PATH})',
    )
    args = parser.parse_args()

    init_db(db_path=args.db_path)


if __name__ == '__main__':
    main()
