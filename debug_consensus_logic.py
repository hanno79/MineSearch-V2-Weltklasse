"""
Debug script to test consensus logic for empty fields
"""
import sys
sys.path.append('/app/backend')

from minesearch.search_utils import is_empty_value
from minesearch.extraction_validators import is_placeholder_value

def test_consensus_calculation():
    """Test the confidence calculation logic"""
    print("=== CONSENSUS LOGIC DEBUG TEST ===")
    
    # Test various empty/placeholder values
    test_values = [
        "X",
        "LEER",
        "Leer", 
        "Unbekannt",
        "N/A",
        "Nichts gefunden",
        "Keine spezifischen Daten dokumentiert",
        "Echte Mine Daten",
        "",
        "Betreiber AG",
        "1234.56",
        "Gold"
    ]
    
    for value in test_values:
        is_empty = is_empty_value(value)
        is_placeholder = is_placeholder_value(value)
        
        # Simulate scoring calculation from consolidated_results.py
        frequency_score = 1.0  # Assume frequency = 1
        source_diversity_score = 0.0  # Assume no diversity
        model_consensus_score = 1.0  # Assume 1 model
        quality_score = 0.0  # Assume no quality
        
        if is_empty:
            non_x_bonus = -100.0  # Empty value malus
        elif is_placeholder:
            non_x_bonus = -50.0  # Placeholder malus  
        else:
            non_x_bonus = 50.0  # Real data bonus
        
        duration_penalty = 0.0  # No penalty
        
        total_score = (frequency_score + source_diversity_score + 
                      model_consensus_score + quality_score + 
                      non_x_bonus + duration_penalty)
        
        # Normalize to 0-100 confidence
        max_reasonable_score = 60.0
        confidence_score = min(100, max(0, (total_score / max_reasonable_score) * 100))
        
        print(f"Value: '{value}'")
        print(f"  is_empty: {is_empty}, is_placeholder: {is_placeholder}")
        print(f"  total_score: {total_score}, confidence: {confidence_score}%")
        print()

if __name__ == "__main__":
    test_consensus_calculation()