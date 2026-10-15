import json
import sys
sys.path.append('.')
from app.core.synthetic.config import SUPPLIER_LATENT_FACTORS, BUYER_LATENT_FACTORS

def normalize_to_100(factors_map):
    # Reverse mapping: Criterion -> {Factor: Weight}
    crit_map = {}
    for factor, criteria_dict in factors_map.items():
        for crit, weight in criteria_dict.items():
            if crit not in crit_map:
                crit_map[crit] = {}
            crit_map[crit][factor] = weight
            
    # Normalize
    normalized_output = {}
    for crit, factors in crit_map.items():
        total = sum(factors.values())
        normalized_output[crit] = {f: round((w/total)*100, 1) for f, w in factors.items()}
        
    return normalized_output

print("--- NORMALIZED SUPPLIER CRITERIA (Sums to 100%) ---")
sup_norm = normalize_to_100(SUPPLIER_LATENT_FACTORS)
for crit, factors in sorted(sup_norm.items()):
    factors_str = " + ".join([f"{w}% {f.replace('_', ' ').title()}" for f, w in factors.items()])
    print(f"- {crit}: {factors_str}")

print("\n--- NORMALIZED BUYER CRITERIA (Sums to 100%) ---")
buy_norm = normalize_to_100(BUYER_LATENT_FACTORS)
for crit, factors in sorted(buy_norm.items()):
    factors_str = " + ".join([f"{w}% {f.replace('_', ' ').title()}" for f, w in factors.items()])
    print(f"- {crit}: {factors_str}")

