#!/usr/bin/env python3
"""Debug CSV column detection"""
import pandas as pd
import sys

def debug_csv(file_path):
    """Debug CSV file column detection"""
    print(f"\n=== Debugging CSV: {file_path} ===\n")
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        print(f"1. Raw columns from pandas:")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Column types: {[type(col).__name__ for col in df.columns]}")
        print(f"   Column repr: {[repr(col) for col in df.columns]}")
        
        # Check for hidden characters
        print(f"\n2. Checking for hidden characters:")
        for i, col in enumerate(df.columns):
            print(f"   Column {i}: '{col}' -> ASCII: {[ord(c) for c in col]}")
        
        # After stripping
        df.columns = df.columns.str.strip()
        print(f"\n3. After stripping whitespace:")
        print(f"   Columns: {list(df.columns)}")
        
        # Check against variants
        mine_name_variants = ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine', 'MINE_NAME', 'NAME']
        print(f"\n4. Checking against mine name variants:")
        found = False
        for variant in mine_name_variants:
            in_columns = variant in df.columns
            print(f"   '{variant}' in columns: {in_columns}")
            if in_columns:
                found = True
                print(f"   ✓ FOUND!")
        
        if not found:
            print(f"\n5. No match found! Possible issues:")
            print(f"   - Case sensitivity")
            print(f"   - Hidden Unicode characters")
            print(f"   - Different encoding")
            
            # Try case-insensitive search
            print(f"\n6. Case-insensitive search:")
            lower_cols = [col.lower() for col in df.columns]
            for variant in mine_name_variants:
                if variant.lower() in lower_cols:
                    idx = lower_cols.index(variant.lower())
                    print(f"   Found '{df.columns[idx]}' (matches '{variant}' case-insensitively)")
        
        # Show first few rows
        print(f"\n7. First 3 rows of data:")
        print(df.head(3))
        
    except Exception as e:
        print(f"Error reading CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug_csv(sys.argv[1])
    else:
        print("Usage: python debug_csv.py <csv_file_path>")
        print("\nTesting with sample CSV...")
        
        # Create a test CSV with potential issues
        import io
        test_csv = """Name ,Region,Country
Malartic Mine,Quebec,Canada
Meadowbank Mine,Nunavut,Canada"""
        
        df = pd.read_csv(io.StringIO(test_csv))
        print("Test CSV columns:", list(df.columns))
        print("Column repr:", [repr(col) for col in df.columns])