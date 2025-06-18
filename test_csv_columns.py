#!/usr/bin/env python3
"""Test script to debug CSV column detection issue"""

import pandas as pd
import io

# Test Case 1: Create a sample CSV with "Name" column
test_csv_1 = """Name,Region,Country
Malartic Mine,Quebec,Canada
Goldstrike Mine,Nevada,USA
Super Pit,Western Australia,Australia"""

# Test Case 2: CSV with spaces in column names
test_csv_2 = """ Name , Region , Country 
Malartic Mine,Quebec,Canada
Goldstrike Mine,Nevada,USA"""

# Test Case 3: CSV with trailing spaces
test_csv_3 = """Name ,Region,Country
Malartic Mine,Quebec,Canada"""

# Test Case 4: CSV with BOM (Byte Order Mark)
test_csv_4_with_bom = b'\xef\xbb\xbfName,Region,Country\nMalartic Mine,Quebec,Canada'

def test_column_detection(csv_content, test_name, is_bytes=False):
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")
    
    try:
        # Read CSV
        if is_bytes:
            df = pd.read_csv(io.BytesIO(csv_content))
        else:
            df = pd.read_csv(io.StringIO(csv_content))
        
        print(f"Columns found: {list(df.columns)}")
        print(f"Column representations: {[repr(col) for col in df.columns]}")
        
        # Test the exact logic from streamlit_app.py
        mine_name_variants = ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine', 'MINE_NAME', 'NAME']
        mine_name_col = None
        
        for variant in mine_name_variants:
            if variant in df.columns:
                mine_name_col = variant
                print(f"✓ Found match: '{variant}'")
                break
        
        if not mine_name_col:
            print("✗ No mine name column found!")
            # Let's debug why
            print("\nDebugging column comparison:")
            for col in df.columns:
                print(f"  Column '{col}' (repr: {repr(col)}):")
                for variant in mine_name_variants:
                    print(f"    '{col}' == '{variant}': {col == variant}")
                    print(f"    '{col}' in ['{variant}']: {col in [variant]}")
        
        # Also test strip() behavior
        print("\nColumn names after strip():")
        stripped_columns = [col.strip() for col in df.columns]
        print(f"Stripped columns: {stripped_columns}")
        
        # Test if stripped version would work
        for variant in mine_name_variants:
            if variant in stripped_columns:
                print(f"✓ Would work with strip(): '{variant}'")
                break
                
    except Exception as e:
        print(f"Error: {e}")

# Run all tests
test_column_detection(test_csv_1, "Normal CSV with 'Name' column")
test_column_detection(test_csv_2, "CSV with spaces around column names")
test_column_detection(test_csv_3, "CSV with trailing spaces in column names")
test_column_detection(test_csv_4_with_bom, "CSV with BOM character", is_bytes=True)

# Additional test: What pandas does with column names
print("\n" + "="*60)
print("Pandas column name handling:")
print("="*60)

test_df = pd.DataFrame({' Name ': ['Test'], 'Region': ['Test2']})
print(f"DataFrame columns: {list(test_df.columns)}")
print(f"Column representations: {[repr(col) for col in test_df.columns]}")