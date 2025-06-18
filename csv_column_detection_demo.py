#!/usr/bin/env python3
"""
Demonstration of CSV column detection issue and fix
"""

import pandas as pd
import io

print("CSV Column Detection Issue Demonstration")
print("=" * 50)

# Create a CSV with whitespace in column names (common issue)
csv_with_spaces = """ Name , Region , Country 
Malartic Mine,Quebec,Canada
Goldstrike Mine,Nevada,USA"""

print("\n1. PROBLEM: CSV with spaces in column headers")
print("CSV content:")
print(csv_with_spaces)

# Read the CSV
df = pd.read_csv(io.StringIO(csv_with_spaces))

print("\n2. What pandas sees:")
print(f"Columns: {df.columns.tolist()}")
print(f"Column representations: {[repr(col) for col in df.columns]}")

# The original detection logic
mine_name_variants = ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine', 'MINE_NAME', 'NAME']
found = False
for variant in mine_name_variants:
    if variant in df.columns:
        found = True
        print(f"\n3. Original logic: Found '{variant}' ✓")
        break

if not found:
    print("\n3. Original logic: No 'Name' column found ✗")
    print("   Because ' Name ' != 'Name'")

# The fix
print("\n4. THE FIX: Strip whitespace from column names")
df.columns = df.columns.str.strip()
print(f"Columns after stripping: {df.columns.tolist()}")

# Try detection again
for variant in mine_name_variants:
    if variant in df.columns:
        print(f"\n5. After fix: Found '{variant}' ✓")
        break

print("\n" + "=" * 50)
print("SUMMARY:")
print("- The issue: Pandas preserves whitespace in CSV column names")
print("- The symptom: Column 'Name' not detected when CSV has ' Name '")
print("- The fix: df.columns = df.columns.str.strip()")
print("- Result: Robust column detection that handles whitespace")