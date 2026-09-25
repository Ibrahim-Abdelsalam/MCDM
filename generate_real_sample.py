import pandas as pd
import numpy as np

np.random.seed(42)
n_suppliers = 500 # Realistic Kaggle size

competence = np.clip(np.random.normal(7, 1.5, n_suppliers), 1, 10)
quality = np.clip(np.random.normal(competence, 0.5), 1, 10)
delivery = np.clip(np.random.normal(competence, 1.0), 1, 10)

price_premium = np.random.normal(competence * 1.5, 2.0)
cost_score = 11 - np.clip(price_premium / 2, 1, 10) 

# Fix missing size argument
financial = np.clip(np.random.normal(7.5, 1.2, n_suppliers), 1, 10)
tech = np.clip(np.random.normal(quality, 1.0), 1, 10)
compliance = np.clip(np.random.normal(8.5, 1.0, n_suppliers), 1, 10)
integration = np.clip(np.random.normal(6.5, 1.5, n_suppliers), 1, 10)
experience = np.clip(np.random.normal(6, 2, n_suppliers), 1, 10)

df = pd.DataFrame({
    'Supplier_ID': [f'SUP-{i:03d}' for i in range(1, n_suppliers + 1)],
    'Quality_Score': np.round(quality, 1),
    'Delivery_Rating': np.round(delivery, 1),
    'Cost_Competitiveness': np.round(cost_score, 1),
    'Financial_Health': np.round(financial, 1),
    'Technical_Capacity': np.round(tech, 1),
    'ESG_Compliance': np.round(compliance, 1),
    'ERP_Integration': np.round(integration, 1),
    'Track_Record': np.round(experience, 1)
})

csv_path = 'app/data/buyer/datasets/kaggle_procurement_sample.csv'
df.to_csv(csv_path, index=False)
print(f"Dataset generated at: {csv_path}")
print("\nFirst 5 rows:")
print(df.head().to_string())
print("\nCorrelation matrix (Quality vs Cost):")
print(df[['Quality_Score', 'Cost_Competitiveness', 'Delivery_Rating']].corr())
