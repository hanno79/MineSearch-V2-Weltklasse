#!/usr/bin/env python3
"""Verify the CSV column detection fix"""

import pandas as pd
import io

# Test the fixed logic
def test_fixed_column_detection(csv_content, test_name):
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")
    
    try:
        # Read CSV
        df = pd.read_csv(io.StringIO(csv_content))
        print(f"Original columns: {list(df.columns)}")
        print(f"Column representations: {[repr(col) for col in df.columns]}")
        
        # Apply the fix: strip whitespace from column names
        df.columns = df.columns.str.strip()
        print(f"After stripping: {list(df.columns)}")
        
        # Test the detection logic
        mine_name_variants = ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine', 'MINE_NAME', 'NAME']
        mine_name_col = None
        column_mapping = {}
        
        for variant in mine_name_variants:
            if variant in df.columns:
                mine_name_col = variant
                column_mapping['mine_name'] = variant
                print(f"✓ Found match: '{variant}'")
                break
        
        if not mine_name_col:
            print("✗ No mine name column found!")
        else:
            print(f"✓ Successfully mapped column: {column_mapping}")
            
    except Exception as e:
        print(f"Error: {e}")

# Test cases that previously failed
test_cases = [
    ("Name,Region,Country\nMalartic Mine,Quebec,Canada", "Normal 'Name' column"),
    (" Name , Region , Country \nMalartic Mine,Quebec,Canada", "Spaces around column names"),
    ("Name ,Region,Country\nMalartic Mine,Quebec,Canada", "Trailing space in 'Name' column"),
    ("  Name,Region,Country\nMalartic Mine,Quebec,Canada", "Leading spaces in 'Name' column"),
    ("name,region,country\nMalartic Mine,Quebec,Canada", "Lowercase 'name' column"),
    ("Mine Name,Region,Country\nMalartic Mine,Quebec,Canada", "Column named 'Mine Name'"),
    ("MINE_NAME,REGION,COUNTRY\nMalartic Mine,Quebec,Canada", "Uppercase with underscore"),
]

for csv_content, description in test_cases:
    test_fixed_column_detection(csv_content, description)

# Test edge cases
print(f"\n{'='*60}")
print("Edge Case Tests")
print(f"{'='*60}")

# Test with tabs
tab_csv = "Name\tRegion\tCountry\nMalartic Mine\tQuebec\tCanada"
df = pd.read_csv(io.StringIO(tab_csv), sep='\t')
df.columns = df.columns.str.strip()
print(f"Tab-separated CSV columns after strip: {list(df.columns)}")

# Test with quotes
quote_csv = '"Name","Region","Country"\n"Malartic Mine","Quebec","Canada"'
df = pd.read_csv(io.StringIO(quote_csv))
df.columns = df.columns.str.strip()
print(f"Quoted CSV columns after strip: {list(df.columns)}")

# Test with mixed whitespace
mixed_csv = "  Name  ,\tRegion\t,Country  \nMalartic Mine,Quebec,Canada"
df = pd.read_csv(io.StringIO(mixed_csv))
print(f"Mixed whitespace - original: {[repr(col) for col in df.columns]}")
df.columns = df.columns.str.strip()
print(f"Mixed whitespace - after strip: {list(df.columns)}")