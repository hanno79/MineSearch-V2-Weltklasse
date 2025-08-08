#!/usr/bin/env python3
import requests
import json

def test_eleonore_data():
    try:
        response = requests.get("http://localhost:8000/api/results/consolidated?days_back=30")
        data = response.json()
        
        if not data['success']:
            print("❌ API error")
            return
            
        results = data['data']['consolidated_results']
        eleonore = None
        
        # Find Éléonore mine
        for result in results:
            if 'Éléonore' in result['mine_name'] or 'eleonore' in result['mine_name'].lower():
                eleonore = result
                break
        
        if not eleonore:
            print("❌ Éléonore mine not found")
            print("Available mines:", [r['mine_name'] for r in results[:5]])
            return
        
        print("✅ Found Éléonore mine")
        print(f"Mine name: {eleonore['mine_name']}")
        print(f"Total fields in best_values: {len(eleonore['best_values'])}")
        
        # Count fields with actual data vs X values
        best_values = eleonore['best_values']
        non_x_fields = [k for k, v in best_values.items() if v != 'X' and not k.startswith('_')]
        x_fields = [k for k, v in best_values.items() if v == 'X']
        
        print(f"Fields with actual data (not X): {len(non_x_fields)}")
        print(f"Fields with X: {len(x_fields)}")
        print(f"Overall confidence: {eleonore.get('overall_confidence', 'N/A')}%")
        
        print("\nFields with actual data:")
        for field in non_x_fields[:10]:
            value = best_values[field]
            display_value = value[:50] + "..." if len(str(value)) > 50 else value
            print(f"  {field}: {display_value}")
        
        # Check for duplicate Mine/Land fields
        field_names = list(best_values.keys())
        mine_fields = [f for f in field_names if 'mine' in f.lower()]
        land_fields = [f for f in field_names if 'land' in f.lower() or 'country' in f.lower()]
        
        print(f"\nDuplicate field check:")
        print(f"Mine-related fields: {mine_fields}")
        print(f"Land/Country-related fields: {land_fields}")
        
        if len(mine_fields) > 1:
            print("⚠️  Warning: Multiple mine fields detected")
        else:
            print("✅ No duplicate mine fields")
            
        if len(land_fields) > 1:
            print("⚠️  Warning: Multiple land/country fields detected")  
        else:
            print("✅ No duplicate land/country fields")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_eleonore_data()