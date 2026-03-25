import argparse
import sys
import os

# Add src to sys.path to allow relative imports within the src package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.setup import main as setup_db
from database.ingest import main as ingest_data
import check_vnexpress
import check_tuoitre

def main():
    parser = argparse.ArgumentParser(
        description="AI News Content Analysis - Central CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: setup
    subparsers.add_parser("setup", help="Initialize or reset the database")

    # Command: ingest
    ingest_parser = subparsers.add_parser("ingest", help="Crawl and store news articles")
    ingest_parser.add_argument(
        "--source", 
        choices=["vnexpress", "tuoitre", "all"], 
        default="all",
        help="Source to crawl (default: all)"
    )
    ingest_parser.add_argument(
        "--limit", 
        type=int, 
        default=50,
        help="Limit articles per source (default: 50)"
    )

    # Command: check
    subparsers.add_parser("check", help="Run crawler verification tests")

    args = parser.parse_args()

    if args.command == "setup":
        print("🚀 Initializing database...")
        sys.argv = [sys.argv[0]] # Clear arguments for setup.py
        setup_db()
    elif args.command == "ingest":
        print(f"📥 Starting ingestion (source={args.source}, limit={args.limit})...")
        sys.argv = [sys.argv[0], "--source", args.source, "--limit", str(args.limit)]
        ingest_data()
    elif args.command == "check":
        print("🔍 Running crawler verification tests...")
        # check scripts don't use argparse usually, but let's be safe
        sys.argv = [sys.argv[0]]
        print("\n--- Checking VNExpress ---")
        check_vnexpress.main()
        print("\n--- Checking TuoiTre ---")
        check_tuoitre.main()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
