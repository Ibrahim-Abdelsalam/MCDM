# Multi-Criteria Decision Support System (MCDM DSS)

A bidirectional evaluation platform for **Supplier and Buyer Selection** using three proven MCDM methods: **AHP**, **TOPSIS**, and **VIKOR**.

## Overview

This system enables organizations to:
- **Evaluate suppliers** from a buyer's perspective using 9 criteria
- **Evaluate buyers** from a supplier's perspective using 9 criteria
- **Apply multiple MCDM methods** and compare results
- **Customize weight schemes** for different evaluation scenarios
- **Generate professional reports** in Excel with visualizations

## System Architecture

```
/app
├── main.py                    # Streamlit UI entry point
├── config.py                  # Shared configuration
├── /core                      # MCDM computation engines
│   ├── criteria.py           # Fixed evaluation criteria
│   ├── company_manager.py    # Company data persistence
│   ├── weight_manager.py     # Weight scheme management
│   ├── dataset_generator.py  # Synthetic data generation
│   ├── normalizer.py         # Data normalization utilities
│   ├── ahp.py               # AHP solver
│   ├── topsis.py            # TOPSIS solver
│   ├── vikor.py             # VIKOR solver
│   └── solver_engine.py     # Analysis orchestrator
└── /export                    # Report generation
    ├── excel_exporter.py     # Excel workbook generation
    └── chart_generator.py    # Chart visualization

/data
├── /supplier
│   ├── /companies          # Supplier JSON records
│   ├── /weights            # Weight scheme files
│   ├── /datasets           # Generated CSV datasets
│   └── /results            # Analysis outputs
└── /buyer
    ├── /companies
    ├── /weights
    ├── /datasets
    └── /results

/tests
└── integration_test.py       # End-to-end validation
```

## Installation

### Prerequisites
- Python 3.9+
- pip or conda

### Quick Setup

```bash
# Clone or navigate to the project
cd MCDM_System

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m tests.integration_test
```

## Usage

### Running the Web UI

```bash
streamlit run app/main.py
```

The UI opens at `http://localhost:8501` with 5 pages:

1. **🏠 Home** — System overview and statistics
2. **🏢 Manage Companies** — Add/remove supplier or buyer records
3. **⚖️ Manage Weight Schemes** — Create/delete custom weight profiles
4. **⚙️ Generate Test Data** — Create synthetic datasets for testing
5. **🚀 Run Analysis** — Execute MCDM analysis and export results

### Programmatic Usage

```python
from app.core.dataset_generator import DatasetGenerator
from app.core.solver_engine import MCDMSolverEngine
from app.core.weight_manager import WeightSchemeManager

# Generate synthetic suppliers
generator = DatasetGenerator()
dataset = generator.generate("supplier", n=50, seed=42)

# Create a weight scheme
weight_mgr = WeightSchemeManager()
weight_mgr.save_scheme("supplier", "Equal Weights", 
    {criterion: 1.0 for criterion in [...]}
)

# Run analysis
engine = MCDMSolverEngine()
results = engine.run_analysis(
    "supplier",
    dataset,
    ["Equal Weights"],
    ["AHP", "TOPSIS", "VIKOR"],
    v=0.5
)
```

## Evaluation Criteria

### Supplier Criteria (9 factors)
1. Quality Performance
2. Delivery Performance
3. Cost Competitiveness *(cost criterion)*
4. Financial Stability
5. Technical Capability
6. Compliance & Sustainability
7. Systems Integration
8. Flexibility
9. Experience & Track Record

### Buyer Criteria (9 factors)
1. Financial Stability & Creditworthiness
2. Payment Performance
3. Order Volume & Growth Potential
4. Demand Stability & Predictability
5. Responsiveness & Collaboration
6. Compliance & Regulatory Standards
7. Technical Sophistication & Systems Integration
8. Market Reputation & Brand Impact
9. Long-Term Strategic Value

## MCDM Methods

### AHP (Analytical Hierarchy Process)
- **Normalization**: Min-max per criterion
- **Scoring**: Weighted average of normalized scores
- **Ranking**: Descending by composite score

### TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
- **Normalization**: Vector normalization (Euclidean)
- **Method**: Distance to ideal and anti-ideal solutions
- **Scoring**: C_i = D- / (D+ + D-)

### VIKOR (VlseKriterijumska Optimizacija I Kompromisno Resenje)
- **Normalization**: Min-max per criterion
- **Method**: Group utility (S) and individual regret (R)
- **Parameter**: v ∈ [0, 1] (0=regret-averse, 1=utility-focused)
- **Scoring**: Inverted Q-index for consistency with AHP/TOPSIS

## Output Formats

### Excel Reports
- **Sheet per method**: Rank, Company_ID, Score (sorted by rank)
- **Summary sheet**: Top 5 across all method-scheme combinations
- **Formatting**: Colored headers, highlighted top 10 rows

### Visualizations (PNG)
- **Bar charts**: Top 10 per method-scheme (method-specific colors)
- **Scatter plots**: Cross-scheme comparison per method

## File Storage

All data stored as **JSON** (companies, weight schemes) or **CSV** (datasets):

```
# Company record
{
  "company_name": "Acme Corp",
  "entity_type": "supplier",
  "scores": {
    "Quality Performance": 8,
    "Delivery Performance": 7,
    ...
  }
}

# Weight scheme
{
  "scheme_name": "Balanced",
  "entity_type": "supplier",
  "weights": {
    "Quality Performance": 10,
    "Delivery Performance": 10,
    ...
  }
}
```

## Integration Test

Verify complete system functionality:

```bash
python -m tests.integration_test
```

Expected output:
- ✓ 50 synthetic suppliers generated
- ✓ Weight scheme created and normalized
- ✓ All 3 MCDM methods executed
- ✓ Excel report generated (11+ KB)
- ✓ 6 visualization charts produced

## Configuration

Edit `app/config.py` to customize:
- `BASE_DIR` — Application root directory
- `SCORE_MIN` / `SCORE_MAX` — Evaluation score range
- `DEFAULT_VIKOR_V` — Default VIKOR v parameter

## Known Limitations

- Max 10,000 entities per analysis
- Criterion names fixed (cannot be customized)
- Single criterion type per entity (all benefit/cost pre-defined)
- Local file storage only (no database)

## Future Enhancements

- Multi-language support
- Database backend (PostgreSQL)
- REST API for external integrations
- Advanced sensitivity analysis
- Collaborative decision-making features

## License

Proprietary — Based on Thesis Project

---

**Version**: 1.0.0  
**Last Updated**: May 2026
