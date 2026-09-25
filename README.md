# A Bidirectional MCDM-Machine Learning Framework for Supplier-Buyer Evaluation

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Academic](https://img.shields.io/badge/Status-Academic_Research-orange.svg)]()

> **Note:** This repository houses the codebase for an advanced academic research project aimed at revolutionizing supply chain procurement. It transitions traditional, unilateral supplier selection into a **dynamic, bi-directional matching problem** utilizing Multi-Criteria Decision Making (MCDM), Machine Learning (ML), Reinforcement Learning (RL), and Blockchain technologies.

## 1. About

Traditional procurement models assume a one-way evaluation framework wherein the buyer exclusively selects the optimal supplier. However, in constrained or competitive markets, suppliers concurrently prioritize buyers based on payment reliability, order volume, and strategic value. 

This framework acts as a "two-sided matching engine" (conceptually similar to the Gale-Shapley algorithm). It evaluates suppliers from the buyer's perspective, evaluates buyers from the supplier's perspective, and mathematically determines stable, mutually beneficial matches.

## 2. Key Features (Current Implementation)

The current core of the application features a robust, mathematically verified MCDM engine wrapped in a professional PyQt6 desktop interface:

* **Fuzzy AHP (Analytic Hierarchy Process):** Handles expert uncertainty using Triangular Fuzzy Numbers (TFN) and Buckley's geometric mean method, verified with formal Consistency Ratio (CR) checks.
* **TOPSIS:** Ranks alternatives based on Euclidean distance to the Positive Ideal Solution (PIS) and Negative Ideal Solution (NIS) utilizing vector normalization.
* **VIKOR:** Provides a compromise ranking by evaluating maximum group utility ($S$) and minimum individual regret ($R$), strictly enforcing acceptable advantage and stability conditions.
* **Bi-Directional GUI:** A PyQt6 desktop dashboard allowing users to switch roles between Buyer and Supplier, manage profiles, run parallel solvers, and generate comprehensive Excel and chart-based reports.

## 3. Evaluation Criteria

The model evaluates entities across two distinct criteria sets to accurately capture the differing priorities and risk profiles of buyers and suppliers:

**Supplier Evaluation Criteria (Buyer's Perspective):**
1. Quality Performance
2. Delivery Performance
3. Cost Competitiveness (Cost criterion)
4. Financial Stability
5. Technical Capability
6. Compliance \& Sustainability
7. Systems Integration
8. Experience \& Track Record

**Buyer Evaluation Criteria (Supplier's Perspective):**
1. Financial Stability \& Creditworthiness
2. Payment Performance
3. Order Volume \& Growth Potential
4. Demand Stability \& Predictability
5. Responsiveness \& Collaboration
6. Compliance \& Regulatory Standards
7. Tech. Sophistication \& Systems Integration
8. Market Reputation
9. Long-Term Strategic Value

## 4. Installation and Usage

### Prerequisites
* Python 3.9+
* macOS / Linux / Windows

### Setup
```bash
# Clone the repository
git clone https://github.com/YourUsername/MCDM-Framework.git
cd MCDM-Framework

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
Launch the PyQt6 desktop dashboard:
```bash
python app/main.py
```

## 5. Academic Citation
*(Placeholder for future publication details: "A Bidirectional MCDM-Machine Learning Framework for Supplier-Buyer Evaluation and Selection")*
