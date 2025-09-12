#!/usr/bin/env python3
"""
Author: rahn
Datum: 03.09.2025
Version: 1.0
Beschreibung: Check search_results table status
"""

from minesearch.database import db_manager
from minesearch.database.models import SearchResult
from sqlalchemy import text, func

def check_search_results():
    """Check search_results table entries"""

    with db_manager.get_session() as session:
        # Count entries using ORM
        count = session.query(SearchResult).count()
        print(f"🔍 search_results count: {count}")

        # Show latest entries using ORM
        print("\n📋 Latest entries:")
        try:
            results = session.query(SearchResult).order_by(SearchResult.created_at.desc()).limit(5).all()
            for result in results:
                print(f"  ID: {result.id}, Mine: {result.mine_name}, Model: {result.model_used},
Created: {result.created_at}")
        except Exception as e:
            print(f"Error reading search_results: {e}")

if __name__ == "__main__":
    check_search_results()
