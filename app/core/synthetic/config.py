"""
Master configuration for the synthetic data generation platform.

Every generator module imports its parameters from this single file.
Organised in 11 sections – each clearly delimited.

Changing a value here propagates through the entire pipeline.
"""

from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 · GENERATION DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_SEED: int = 42
DEFAULT_YEAR_START: int = 2018
DEFAULT_YEAR_END: int = 2026
DEFAULT_N_SUPPLIERS: int = 200
DEFAULT_N_BUYERS: int = 80
SCORE_MIN: int = 1
SCORE_MAX: int = 10
GRANULARITY: str = "quarterly"          # "monthly", "quarterly", or "yearly"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 · CRITERIA DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

SUPPLIER_CRITERIA: list[dict[str, str]] = [
    {
        "name": "Quality Performance",
        "type": "benefit",
        "description": "Consistency in meeting quality specifications and defect rates",
    },
    {
        "name": "Compliance and Sustainability",
        "type": "benefit",
        "description": (
            "Regulatory compliance, environmental standards, social responsibility, "
            "cybersecurity measures and ethical standards"
        ),
    },
    {
        "name": "Cost / Price Competitiveness",
        "type": "cost",
        "description": "Unit pricing, cost stability and negotiation flexibility",
    },
    {
        "name": "Delivery Performance",
        "type": "benefit",
        "description": "Consistency, reliability and responsiveness of delivery",
    },
    {
        "name": "Experience and Track Record",
        "type": "benefit",
        "description": "Reliability and risk reduction based on historical experience",
    },
    {
        "name": "Financial Stability",
        "type": "benefit",
        "description": "Long-term supplier viability and exposure to disruption",
    },
    {
        "name": "Flexibility",
        "type": "benefit",
        "description": (
            "Ability to accommodate demand fluctuations, order changes "
            "and emergency requests"
        ),
    },
    {
        "name": "Systems Integration",
        "type": "benefit",
        "description": "ERP compatibility, data sharing, traceability and reporting",
    },
    {
        "name": "Technical Capability / Process Capability",
        "type": "benefit",
        "description": (
            "Production technology, process control and ability to meet specifications"
        ),
    },
]

BUYER_CRITERIA: list[dict[str, str]] = [
    {
        "name": "Compliance & Regulatory Standards",
        "type": "benefit",
        "description": "Legal, tax and regulatory adherence",
    },
    {
        "name": "Demand Stability & Predictability",
        "type": "benefit",
        "description": "Forecast accuracy and order consistency",
    },
    {
        "name": "Financial Stability & Creditworthiness",
        "type": "benefit",
        "description": "Long-term financial health of the buyer",
    },
    {
        "name": "Long-Term Strategic Value",
        "type": "benefit",
        "description": "Strategic importance to supplier growth",
    },
    {
        "name": "Market Reputation & Brand Impact",
        "type": "benefit",
        "description": "Buyer's influence on supplier brand image",
    },
    {
        "name": "Order Volume & Growth Potential",
        "type": "benefit",
        "description": "Current and future revenue contribution",
    },
    {
        "name": "Payment Performance",
        "type": "benefit",
        "description": "Historical payment behavior",
    },
    {
        "name": "Responsiveness & Collaboration",
        "type": "benefit",
        "description": "Speed and effectiveness of communication",
    },
    {
        "name": "Technical Sophistication (Systems)",
        "type": "benefit",
        "description": "ERP, EDI and digital integration capability",
    },
]

SUPPLIER_CRITERIA_NAMES: list[str] = [c["name"] for c in SUPPLIER_CRITERIA]
BUYER_CRITERIA_NAMES: list[str] = [c["name"] for c in BUYER_CRITERIA]
N_SUPPLIER_CRITERIA: int = len(SUPPLIER_CRITERIA_NAMES)
N_BUYER_CRITERIA: int = len(BUYER_CRITERIA_NAMES)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 · QUALIFICATION GATES
# ═══════════════════════════════════════════════════════════════════════════════

SUPPLIER_GATES: list[dict[str, str]] = [
    {
        "name": "Quality Compliance",
        "description": "Meets minimum quality standards",
        "linked_criterion": "Quality Performance",
    },
    {
        "name": "Regulatory / ESG Compliance",
        "description": "Meets regulatory, environmental, social, governance requirements",
        "linked_criterion": "Compliance and Sustainability",
    },
    {
        "name": "HSE",
        "description": "Health, Safety & Environment clearance",
        "linked_criterion": "Compliance and Sustainability",
    },
    {
        "name": "Capacity / MOQ Compatibility",
        "description": "Can meet minimum order quantities and capacity needs",
        "linked_criterion": "Flexibility",
    },
]

BUYER_GATES: list[dict[str, str]] = [
    {
        "name": "Compliance & Regulatory Standards",
        "description": "Legal, tax and regulatory adherence",
        "linked_criterion": "Compliance & Regulatory Standards",
    },
    {
        "name": "Financial Stability & Creditworthiness",
        "description": "Long-term financial health",
        "linked_criterion": "Financial Stability & Creditworthiness",
    },
]

# Default gate-pass threshold: score >= this value → pass
GATE_PASS_THRESHOLD: float = 4.0


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 · AHP CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SAATY_SCALE: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9]

SAATY_RI: dict[int, float] = {
    1:  0.00,
    2:  0.00,
    3:  0.58,
    4:  0.90,
    5:  1.12,
    6:  1.24,
    7:  1.32,
    8:  1.41,
    9:  1.45,
    10: 1.49,
}

CR_THRESHOLD: float = 0.10

CR_BANDS: dict[str, tuple[float, float]] = {
    "highly_consistent":       (0.00, 0.05),
    "acceptable":              (0.05, 0.10),
    "moderately_inconsistent": (0.10, 0.20),
    "strongly_inconsistent":   (0.20, 1.00),
}

DEFAULT_CR_DISTRIBUTION: dict[str, float] = {
    "highly_consistent":       0.80,
    "acceptable":              0.20,
    "moderately_inconsistent": 0.00,
    "strongly_inconsistent":   0.00,
}

MAX_REPAIR_ITERATIONS: int = 50


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 · DIRECT WEIGHT SCALE
# ═══════════════════════════════════════════════════════════════════════════════

DIRECT_WEIGHT_BANDS: list[tuple[int, int, str]] = [
    (1,  2,  "Minimal importance"),
    (3,  4,  "Low importance"),
    (5,  6,  "Moderate importance"),
    (7,  8,  "High importance"),
    (9,  10, "Critical importance"),
]


def get_weight_interpretation(value: float) -> str:
    """Return the interpretation label for a raw direct weight value."""
    rounded = round(value)
    for lo, hi, label in DIRECT_WEIGHT_BANDS:
        if lo <= rounded <= hi:
            return label
    return "Unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 · ENTITY ATTRIBUTES
# ═══════════════════════════════════════════════════════════════════════════════

COMPANY_SIZES: dict[str, dict] = {
    "Small": {
        "employee_range": (10, 49),
        "revenue_bands": ["$1M-5M", "$5M-10M"],
    },
    "Medium": {
        "employee_range": (50, 249),
        "revenue_bands": ["$10M-25M", "$25M-50M"],
    },
    "Large": {
        "employee_range": (250, 999),
        "revenue_bands": ["$50M-100M", "$100M-500M"],
    },
    "Enterprise": {
        "employee_range": (1000, 50000),
        "revenue_bands": ["$500M-1B", "$1B+"],
    },
}

REGIONS: dict[str, list[str]] = {
    "Europe": [
        "Germany", "UK", "France", "Netherlands", "Italy",
        "Spain", "Poland", "Sweden", "Switzerland",
    ],
    "North America": ["USA", "Canada", "Mexico"],
    "Asia Pacific": [
        "China", "Japan", "South Korea", "India", "Taiwan",
        "Singapore", "Thailand", "Vietnam",
    ],
    "Middle East": ["UAE", "Saudi Arabia", "Turkey", "Jordan"],
    "South America": ["Brazil", "Argentina", "Chile"],
    "Africa": ["South Africa", "Nigeria", "Kenya", "Egypt"],
}

STRATEGIC_SEGMENTS: list[str] = ["Strategic", "Leverage", "Bottleneck", "Routine"]
RISK_SEGMENTS: list[str] = ["Low", "Medium", "High", "Critical"]

CONTRACT_TYPES: list[str] = ["Spot", "Annual", "Multi-Year", "Framework"]
ORDER_FREQUENCIES: list[str] = ["Weekly", "Bi-Weekly", "Monthly", "Quarterly"]
PAYMENT_TERMS: list[str] = ["Net 15", "Net 30", "Net 45", "Net 60", "Net 90"]
RELATIONSHIP_STATUSES: list[str] = [
    "Active", "Inactive", "Terminated", "On Hold", "Under Review",
]
RELATIONSHIP_QUALITY_LEVELS: list[str] = [
    "Excellent", "Acceptable", "Weak", "Failed", "Terminated",
]

# Data-source labels for entity ratings
DATA_SOURCES: list[str] = [
    "audit", "survey", "self-assessment", "system-extracted",
    "third-party-report", "site-visit",
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 · INDUSTRY PROFILES
#
# Each profile defines:
#   supplier_weight_tendencies  – (mean, std) per supplier criterion
#   buyer_weight_tendencies     – (mean, std) per buyer criterion
#   score_adjustments           – additive shift to baseline scores
#   mandatory_supplier_gates    – always enforced
#   optional_supplier_gates     – enforced in some scenarios
#   mandatory_buyer_gates       – always enforced
#   optional_buyer_gates        – enforced in some scenarios
#   gate_pass_rate              – base probability of passing gates
#   seasonal_amplitude          – 0.0–0.30 magnitude of seasonality
#   seasonal_peak_quarters      – which quarters peak
#   risk_volatility             – year-over-year score drift magnitude
#   typical_company_sizes       – probability distribution over sizes
#   primary_regions             – most probable regions
# ═══════════════════════════════════════════════════════════════════════════════

INDUSTRY_PROFILES: dict[str, dict] = {

    # ── FMCG ────────────────────────────────────────────────────────────────
    "FMCG": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (7.0, 1.0),
            "Compliance and Sustainability":            (5.5, 1.2),
            "Cost / Price Competitiveness":             (8.0, 1.0),
            "Delivery Performance":                     (8.5, 0.8),
            "Experience and Track Record":              (5.5, 1.2),
            "Financial Stability":                      (6.0, 1.0),
            "Flexibility":                              (8.0, 1.0),
            "Systems Integration":                      (6.0, 1.2),
            "Technical Capability / Process Capability": (5.5, 1.0),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (5.5, 1.2),
            "Demand Stability & Predictability":        (6.5, 1.0),
            "Financial Stability & Creditworthiness":   (7.0, 1.0),
            "Long-Term Strategic Value":                (5.5, 1.2),
            "Market Reputation & Brand Impact":         (7.5, 1.0),
            "Order Volume & Growth Potential":          (8.5, 0.8),
            "Payment Performance":                      (8.0, 1.0),
            "Responsiveness & Collaboration":           (7.5, 1.0),
            "Technical Sophistication (Systems)":       (5.0, 1.2),
        },
        "score_adjustments": {
            "Delivery Performance": +0.5,
            "Flexibility": +0.5,
            "Cost / Price Competitiveness": +0.3,
        },
        "mandatory_supplier_gates": ["Quality Compliance", "Regulatory / ESG Compliance"],
        "optional_supplier_gates": ["Capacity / MOQ Compatibility"],
        "mandatory_buyer_gates": ["Compliance & Regulatory Standards"],
        "optional_buyer_gates": ["Financial Stability & Creditworthiness"],
        "gate_pass_rate": 0.85,
        "seasonal_amplitude": 0.20,
        "seasonal_peak_quarters": [4],
        "risk_volatility": 0.12,
        "typical_company_sizes": {"Small": 0.30, "Medium": 0.40, "Large": 0.20, "Enterprise": 0.10},
        "primary_regions": ["Europe", "North America", "Asia Pacific"],
    },

    # ── Food & Beverage ─────────────────────────────────────────────────────
    "Food & Beverage": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (9.0, 0.8),
            "Compliance and Sustainability":            (8.5, 0.8),
            "Cost / Price Competitiveness":             (6.5, 1.0),
            "Delivery Performance":                     (8.0, 0.8),
            "Experience and Track Record":              (6.5, 1.0),
            "Financial Stability":                      (7.0, 1.0),
            "Flexibility":                              (6.0, 1.2),
            "Systems Integration":                      (5.5, 1.2),
            "Technical Capability / Process Capability": (6.5, 1.0),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (8.5, 0.8),
            "Demand Stability & Predictability":        (7.0, 1.0),
            "Financial Stability & Creditworthiness":   (7.0, 1.0),
            "Long-Term Strategic Value":                (5.5, 1.2),
            "Market Reputation & Brand Impact":         (6.5, 1.0),
            "Order Volume & Growth Potential":          (7.5, 1.0),
            "Payment Performance":                      (7.0, 1.0),
            "Responsiveness & Collaboration":           (6.5, 1.0),
            "Technical Sophistication (Systems)":       (5.0, 1.2),
        },
        "score_adjustments": {
            "Quality Performance": +1.0,
            "Compliance and Sustainability": +1.0,
            "Delivery Performance": +0.5,
        },
        "mandatory_supplier_gates": [
            "Quality Compliance", "Regulatory / ESG Compliance", "HSE",
        ],
        "optional_supplier_gates": ["Capacity / MOQ Compatibility"],
        "mandatory_buyer_gates": ["Compliance & Regulatory Standards"],
        "optional_buyer_gates": ["Financial Stability & Creditworthiness"],
        "gate_pass_rate": 0.82,
        "seasonal_amplitude": 0.18,
        "seasonal_peak_quarters": [3, 4],
        "risk_volatility": 0.10,
        "typical_company_sizes": {"Small": 0.25, "Medium": 0.40, "Large": 0.25, "Enterprise": 0.10},
        "primary_regions": ["Europe", "North America", "Asia Pacific", "South America"],
    },

    # ── Automotive ──────────────────────────────────────────────────────────
    "Automotive": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (9.5, 0.5),
            "Compliance and Sustainability":            (7.0, 1.0),
            "Cost / Price Competitiveness":             (7.0, 1.0),
            "Delivery Performance":                     (9.0, 0.8),
            "Experience and Track Record":              (7.5, 1.0),
            "Financial Stability":                      (8.0, 0.8),
            "Flexibility":                              (5.5, 1.2),
            "Systems Integration":                      (7.5, 1.0),
            "Technical Capability / Process Capability": (9.0, 0.8),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (7.0, 1.0),
            "Demand Stability & Predictability":        (9.0, 0.8),
            "Financial Stability & Creditworthiness":   (8.0, 0.8),
            "Long-Term Strategic Value":                (7.5, 1.0),
            "Market Reputation & Brand Impact":         (6.5, 1.0),
            "Order Volume & Growth Potential":          (7.5, 1.0),
            "Payment Performance":                      (7.0, 1.0),
            "Responsiveness & Collaboration":           (6.5, 1.0),
            "Technical Sophistication (Systems)":       (8.0, 0.8),
        },
        "score_adjustments": {
            "Quality Performance": +1.0,
            "Technical Capability / Process Capability": +1.0,
            "Delivery Performance": +0.5,
            "Systems Integration": +0.5,
        },
        "mandatory_supplier_gates": [
            "Quality Compliance", "Regulatory / ESG Compliance",
            "HSE", "Capacity / MOQ Compatibility",
        ],
        "optional_supplier_gates": [],
        "mandatory_buyer_gates": [
            "Compliance & Regulatory Standards",
            "Financial Stability & Creditworthiness",
        ],
        "optional_buyer_gates": [],
        "gate_pass_rate": 0.80,
        "seasonal_amplitude": 0.12,
        "seasonal_peak_quarters": [1, 3],
        "risk_volatility": 0.08,
        "typical_company_sizes": {"Small": 0.10, "Medium": 0.30, "Large": 0.35, "Enterprise": 0.25},
        "primary_regions": ["Europe", "North America", "Asia Pacific"],
    },

    # ── Industrial Manufacturing ────────────────────────────────────────────
    "Industrial Manufacturing": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (7.5, 1.0),
            "Compliance and Sustainability":            (6.0, 1.2),
            "Cost / Price Competitiveness":             (8.0, 1.0),
            "Delivery Performance":                     (7.5, 1.0),
            "Experience and Track Record":              (8.0, 0.8),
            "Financial Stability":                      (7.0, 1.0),
            "Flexibility":                              (6.0, 1.2),
            "Systems Integration":                      (7.0, 1.0),
            "Technical Capability / Process Capability": (8.5, 0.8),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (6.0, 1.2),
            "Demand Stability & Predictability":        (7.5, 1.0),
            "Financial Stability & Creditworthiness":   (7.0, 1.0),
            "Long-Term Strategic Value":                (6.5, 1.0),
            "Market Reputation & Brand Impact":         (5.5, 1.2),
            "Order Volume & Growth Potential":          (8.0, 0.8),
            "Payment Performance":                      (7.5, 1.0),
            "Responsiveness & Collaboration":           (6.0, 1.2),
            "Technical Sophistication (Systems)":       (7.0, 1.0),
        },
        "score_adjustments": {
            "Technical Capability / Process Capability": +0.8,
            "Experience and Track Record": +0.5,
        },
        "mandatory_supplier_gates": ["Quality Compliance", "Regulatory / ESG Compliance"],
        "optional_supplier_gates": ["HSE", "Capacity / MOQ Compatibility"],
        "mandatory_buyer_gates": ["Compliance & Regulatory Standards"],
        "optional_buyer_gates": ["Financial Stability & Creditworthiness"],
        "gate_pass_rate": 0.85,
        "seasonal_amplitude": 0.10,
        "seasonal_peak_quarters": [1, 2],
        "risk_volatility": 0.09,
        "typical_company_sizes": {"Small": 0.20, "Medium": 0.35, "Large": 0.30, "Enterprise": 0.15},
        "primary_regions": ["Europe", "North America", "Asia Pacific", "Middle East"],
    },

    # ── Packaging ───────────────────────────────────────────────────────────
    "Packaging": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (8.0, 0.8),
            "Compliance and Sustainability":            (5.5, 1.2),
            "Cost / Price Competitiveness":             (9.0, 0.8),
            "Delivery Performance":                     (8.0, 0.8),
            "Experience and Track Record":              (5.5, 1.2),
            "Financial Stability":                      (6.0, 1.2),
            "Flexibility":                              (9.0, 0.8),
            "Systems Integration":                      (5.0, 1.2),
            "Technical Capability / Process Capability": (6.5, 1.0),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (5.0, 1.2),
            "Demand Stability & Predictability":        (7.0, 1.0),
            "Financial Stability & Creditworthiness":   (6.0, 1.2),
            "Long-Term Strategic Value":                (5.0, 1.2),
            "Market Reputation & Brand Impact":         (5.0, 1.2),
            "Order Volume & Growth Potential":          (8.5, 0.8),
            "Payment Performance":                      (7.5, 1.0),
            "Responsiveness & Collaboration":           (7.0, 1.0),
            "Technical Sophistication (Systems)":       (5.0, 1.2),
        },
        "score_adjustments": {
            "Flexibility": +0.8,
            "Cost / Price Competitiveness": +0.5,
        },
        "mandatory_supplier_gates": ["Quality Compliance"],
        "optional_supplier_gates": [
            "Regulatory / ESG Compliance", "Capacity / MOQ Compatibility",
        ],
        "mandatory_buyer_gates": [],
        "optional_buyer_gates": [
            "Compliance & Regulatory Standards",
            "Financial Stability & Creditworthiness",
        ],
        "gate_pass_rate": 0.88,
        "seasonal_amplitude": 0.15,
        "seasonal_peak_quarters": [3, 4],
        "risk_volatility": 0.11,
        "typical_company_sizes": {"Small": 0.35, "Medium": 0.35, "Large": 0.20, "Enterprise": 0.10},
        "primary_regions": ["Europe", "Asia Pacific", "North America"],
    },

    # ── Pharmaceutical ──────────────────────────────────────────────────────
    "Pharmaceutical": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (9.5, 0.5),
            "Compliance and Sustainability":            (9.5, 0.5),
            "Cost / Price Competitiveness":             (4.5, 1.2),
            "Delivery Performance":                     (8.0, 0.8),
            "Experience and Track Record":              (8.5, 0.8),
            "Financial Stability":                      (8.0, 0.8),
            "Flexibility":                              (5.0, 1.2),
            "Systems Integration":                      (7.5, 1.0),
            "Technical Capability / Process Capability": (8.5, 0.8),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (9.5, 0.5),
            "Demand Stability & Predictability":        (7.0, 1.0),
            "Financial Stability & Creditworthiness":   (8.0, 0.8),
            "Long-Term Strategic Value":                (7.0, 1.0),
            "Market Reputation & Brand Impact":         (7.0, 1.0),
            "Order Volume & Growth Potential":          (6.5, 1.0),
            "Payment Performance":                      (8.0, 0.8),
            "Responsiveness & Collaboration":           (6.0, 1.2),
            "Technical Sophistication (Systems)":       (7.0, 1.0),
        },
        "score_adjustments": {
            "Quality Performance": +1.5,
            "Compliance and Sustainability": +1.5,
            "Technical Capability / Process Capability": +0.8,
            "Experience and Track Record": +0.5,
        },
        "mandatory_supplier_gates": [
            "Quality Compliance", "Regulatory / ESG Compliance",
            "HSE", "Capacity / MOQ Compatibility",
        ],
        "optional_supplier_gates": [],
        "mandatory_buyer_gates": [
            "Compliance & Regulatory Standards",
            "Financial Stability & Creditworthiness",
        ],
        "optional_buyer_gates": [],
        "gate_pass_rate": 0.78,
        "seasonal_amplitude": 0.05,
        "seasonal_peak_quarters": [],
        "risk_volatility": 0.06,
        "typical_company_sizes": {"Small": 0.10, "Medium": 0.25, "Large": 0.35, "Enterprise": 0.30},
        "primary_regions": ["Europe", "North America", "Asia Pacific"],
    },

    # ── Consumer Goods ──────────────────────────────────────────────────────
    "Consumer Goods": {
        "supplier_weight_tendencies": {
            "Quality Performance":                      (7.0, 1.0),
            "Compliance and Sustainability":            (6.0, 1.2),
            "Cost / Price Competitiveness":             (8.0, 1.0),
            "Delivery Performance":                     (8.0, 0.8),
            "Experience and Track Record":              (5.5, 1.2),
            "Financial Stability":                      (6.0, 1.2),
            "Flexibility":                              (7.5, 1.0),
            "Systems Integration":                      (5.5, 1.2),
            "Technical Capability / Process Capability": (5.5, 1.2),
        },
        "buyer_weight_tendencies": {
            "Compliance & Regulatory Standards":        (5.5, 1.2),
            "Demand Stability & Predictability":        (6.5, 1.0),
            "Financial Stability & Creditworthiness":   (6.5, 1.0),
            "Long-Term Strategic Value":                (6.0, 1.2),
            "Market Reputation & Brand Impact":         (8.0, 0.8),
            "Order Volume & Growth Potential":          (8.5, 0.8),
            "Payment Performance":                      (7.0, 1.0),
            "Responsiveness & Collaboration":           (7.5, 1.0),
            "Technical Sophistication (Systems)":       (5.5, 1.2),
        },
        "score_adjustments": {
            "Market Reputation & Brand Impact": +0.5,
            "Flexibility": +0.3,
        },
        "mandatory_supplier_gates": ["Quality Compliance", "Regulatory / ESG Compliance"],
        "optional_supplier_gates": ["Capacity / MOQ Compatibility"],
        "mandatory_buyer_gates": ["Compliance & Regulatory Standards"],
        "optional_buyer_gates": ["Financial Stability & Creditworthiness"],
        "gate_pass_rate": 0.86,
        "seasonal_amplitude": 0.22,
        "seasonal_peak_quarters": [4],
        "risk_volatility": 0.11,
        "typical_company_sizes": {"Small": 0.30, "Medium": 0.35, "Large": 0.25, "Enterprise": 0.10},
        "primary_regions": ["Europe", "North America", "Asia Pacific", "Middle East"],
    },
}

INDUSTRY_NAMES: list[str] = list(INDUSTRY_PROFILES.keys())

# Cross-industry sourcing compatibility (buyer_industry → compatible supplier_industries)
INDUSTRY_COMPATIBILITY: dict[str, list[str]] = {
    "FMCG":                     ["FMCG", "Packaging", "Consumer Goods"],
    "Food & Beverage":          ["Food & Beverage", "Packaging", "Industrial Manufacturing"],
    "Automotive":               ["Automotive", "Industrial Manufacturing", "Packaging"],
    "Industrial Manufacturing": ["Industrial Manufacturing", "Packaging"],
    "Packaging":                ["Packaging", "Industrial Manufacturing"],
    "Pharmaceutical":           ["Pharmaceutical", "Industrial Manufacturing", "Packaging"],
    "Consumer Goods":           ["Consumer Goods", "FMCG", "Packaging"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 · DECISION-MAKER ROLES
#
# Biases are additive modifiers applied on top of the industry baseline.
# Positive = role tends to rate that criterion higher than the industry mean.
# Negative = role tends to rate it lower.
# ═══════════════════════════════════════════════════════════════════════════════

# Buyer-side experts evaluating SUPPLIERS
SUPPLIER_EVAL_ROLES: dict[str, dict[str, dict[str, float]]] = {
    "Procurement": {
        "weight_biases": {
            "Quality Performance":                      +0.0,
            "Compliance and Sustainability":            -0.5,
            "Cost / Price Competitiveness":             +2.0,
            "Delivery Performance":                     +0.5,
            "Experience and Track Record":              +0.0,
            "Financial Stability":                      +1.0,
            "Flexibility":                              +1.5,
            "Systems Integration":                      +0.0,
            "Technical Capability / Process Capability": -0.5,
        },
    },
    "Quality": {
        "weight_biases": {
            "Quality Performance":                      +2.5,
            "Compliance and Sustainability":            +2.0,
            "Cost / Price Competitiveness":             -1.5,
            "Delivery Performance":                     +0.5,
            "Experience and Track Record":              +0.5,
            "Financial Stability":                      +0.0,
            "Flexibility":                              -0.5,
            "Systems Integration":                      +0.5,
            "Technical Capability / Process Capability": +2.0,
        },
    },
    "Supply Chain": {
        "weight_biases": {
            "Quality Performance":                      +0.0,
            "Compliance and Sustainability":            -0.5,
            "Cost / Price Competitiveness":             +0.5,
            "Delivery Performance":                     +2.5,
            "Experience and Track Record":              +0.0,
            "Financial Stability":                      +0.0,
            "Flexibility":                              +2.0,
            "Systems Integration":                      +1.5,
            "Technical Capability / Process Capability": +0.0,
        },
    },
    "Operations": {
        "weight_biases": {
            "Quality Performance":                      +1.0,
            "Compliance and Sustainability":            +0.0,
            "Cost / Price Competitiveness":             +0.0,
            "Delivery Performance":                     +1.5,
            "Experience and Track Record":              +0.5,
            "Financial Stability":                      -0.5,
            "Flexibility":                              +1.0,
            "Systems Integration":                      +0.5,
            "Technical Capability / Process Capability": +2.0,
        },
    },
    "Finance": {
        "weight_biases": {
            "Quality Performance":                      -0.5,
            "Compliance and Sustainability":            +0.5,
            "Cost / Price Competitiveness":             +1.5,
            "Delivery Performance":                     -0.5,
            "Experience and Track Record":              +1.0,
            "Financial Stability":                      +2.5,
            "Flexibility":                              -1.0,
            "Systems Integration":                      +0.0,
            "Technical Capability / Process Capability": -1.0,
        },
    },
}

# Supplier-side experts evaluating BUYERS
BUYER_EVAL_ROLES: dict[str, dict[str, dict[str, float]]] = {
    "Sales": {
        "weight_biases": {
            "Compliance & Regulatory Standards":        -1.0,
            "Demand Stability & Predictability":        +0.0,
            "Financial Stability & Creditworthiness":   +0.5,
            "Long-Term Strategic Value":                +0.5,
            "Market Reputation & Brand Impact":         +2.0,
            "Order Volume & Growth Potential":          +2.5,
            "Payment Performance":                      +0.5,
            "Responsiveness & Collaboration":           +1.0,
            "Technical Sophistication (Systems)":       -1.0,
        },
    },
    "Customer Management": {
        "weight_biases": {
            "Compliance & Regulatory Standards":        +0.0,
            "Demand Stability & Predictability":        +0.5,
            "Financial Stability & Creditworthiness":   +0.0,
            "Long-Term Strategic Value":                +2.0,
            "Market Reputation & Brand Impact":         +1.0,
            "Order Volume & Growth Potential":          +0.0,
            "Payment Performance":                      +0.0,
            "Responsiveness & Collaboration":           +2.5,
            "Technical Sophistication (Systems)":       +0.0,
        },
    },
    "Finance": {
        "weight_biases": {
            "Compliance & Regulatory Standards":        +0.5,
            "Demand Stability & Predictability":        +0.5,
            "Financial Stability & Creditworthiness":   +2.5,
            "Long-Term Strategic Value":                -0.5,
            "Market Reputation & Brand Impact":         -1.0,
            "Order Volume & Growth Potential":          +0.5,
            "Payment Performance":                      +2.5,
            "Responsiveness & Collaboration":           -1.0,
            "Technical Sophistication (Systems)":       +0.0,
        },
    },
    "Commercial": {
        "weight_biases": {
            "Compliance & Regulatory Standards":        -0.5,
            "Demand Stability & Predictability":        +0.5,
            "Financial Stability & Creditworthiness":   +1.0,
            "Long-Term Strategic Value":                +1.5,
            "Market Reputation & Brand Impact":         +0.5,
            "Order Volume & Growth Potential":          +2.0,
            "Payment Performance":                      +1.0,
            "Responsiveness & Collaboration":           +0.0,
            "Technical Sophistication (Systems)":       -0.5,
        },
    },
    "Account Management": {
        "weight_biases": {
            "Compliance & Regulatory Standards":        +0.0,
            "Demand Stability & Predictability":        +2.0,
            "Financial Stability & Creditworthiness":   +0.0,
            "Long-Term Strategic Value":                +1.5,
            "Market Reputation & Brand Impact":         +0.5,
            "Order Volume & Growth Potential":          +0.5,
            "Payment Performance":                      +1.0,
            "Responsiveness & Collaboration":           +2.0,
            "Technical Sophistication (Systems)":       -0.5,
        },
    },
}

SUPPLIER_EVAL_ROLE_NAMES: list[str] = list(SUPPLIER_EVAL_ROLES.keys())
BUYER_EVAL_ROLE_NAMES: list[str] = list(BUYER_EVAL_ROLES.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 · LATENT FACTOR MODEL
#
# Each entity is assigned latent factor scores (drawn from a standard-ish
# distribution).  Factor loadings map latent scores → observable criterion
# scores.  Loading = how strongly that factor drives that criterion.
# ═══════════════════════════════════════════════════════════════════════════════

SUPPLIER_LATENT_FACTORS: dict[str, dict[str, float]] = {
    "operational_capability": {
        "Quality Performance":                      0.85,
        "Delivery Performance":                     0.80,
        "Technical Capability / Process Capability": 0.75,
        "Flexibility":                              0.60,
        "Systems Integration":                      0.25,
    },
    "business_maturity": {
        "Financial Stability":                      0.85,
        "Experience and Track Record":              0.80,
        "Systems Integration":                      0.55,
        "Quality Performance":                      0.20,
        "Compliance and Sustainability":            0.30,
    },
    "compliance_posture": {
        "Compliance and Sustainability":            0.85,
        "Quality Performance":                      0.15,
    },
    "commercial_competitiveness": {
        "Cost / Price Competitiveness":             0.90,
        "Flexibility":                              0.20,
    },
}

BUYER_LATENT_FACTORS: dict[str, dict[str, float]] = {
    "financial_health": {
        "Financial Stability & Creditworthiness":   0.85,
        "Payment Performance":                      0.80,
        "Order Volume & Growth Potential":           0.55,
    },
    "operational_maturity": {
        "Demand Stability & Predictability":        0.80,
        "Technical Sophistication (Systems)":       0.75,
        "Responsiveness & Collaboration":           0.65,
    },
    "strategic_positioning": {
        "Long-Term Strategic Value":                0.85,
        "Market Reputation & Brand Impact":         0.80,
        "Order Volume & Growth Potential":           0.35,
    },
    "compliance_culture": {
        "Compliance & Regulatory Standards":        0.90,
    },
}

# Company-size influence on latent factors (additive shift to factor mean)
SIZE_FACTOR_ADJUSTMENTS: dict[str, dict[str, float]] = {
    "Small":      {"operational_capability": -0.3, "business_maturity": -0.8,
                   "compliance_posture": -0.4, "commercial_competitiveness": +0.2,
                   "financial_health": -0.6, "operational_maturity": -0.5,
                   "strategic_positioning": -0.7, "compliance_culture": -0.4},
    "Medium":     {"operational_capability": +0.0, "business_maturity": +0.0,
                   "compliance_posture": +0.0, "commercial_competitiveness": +0.0,
                   "financial_health": +0.0, "operational_maturity": +0.0,
                   "strategic_positioning": +0.0, "compliance_culture": +0.0},
    "Large":      {"operational_capability": +0.3, "business_maturity": +0.5,
                   "compliance_posture": +0.3, "commercial_competitiveness": -0.1,
                   "financial_health": +0.4, "operational_maturity": +0.4,
                   "strategic_positioning": +0.5, "compliance_culture": +0.3},
    "Enterprise": {"operational_capability": +0.5, "business_maturity": +0.8,
                   "compliance_posture": +0.6, "commercial_competitiveness": -0.3,
                   "financial_health": +0.7, "operational_maturity": +0.6,
                   "strategic_positioning": +0.8, "compliance_culture": +0.5},
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 · TEMPORAL PARAMETERS
#
# persistence  – AR(1) coefficient; 1.0 = no change, 0.0 = fully random
# drift_std    – std of the Gaussian innovation per year
# shock_prob   – probability of a shock event per entity per year
# shock_mag    – (min_negative, max_positive) magnitude of a shock
# ═══════════════════════════════════════════════════════════════════════════════

TEMPORAL_PARAMS: dict[str, dict[str, float | tuple]] = {
    # ── Supplier criteria ───────────────────────────────────────────────
    "Quality Performance":                      {"persistence": 0.92, "drift_std": 0.25, "shock_prob": 0.04, "shock_mag": (-2.0, 1.5)},
    "Compliance and Sustainability":            {"persistence": 0.94, "drift_std": 0.20, "shock_prob": 0.03, "shock_mag": (-1.5, 2.0)},
    "Cost / Price Competitiveness":             {"persistence": 0.88, "drift_std": 0.35, "shock_prob": 0.06, "shock_mag": (-1.5, 1.5)},
    "Delivery Performance":                     {"persistence": 0.90, "drift_std": 0.30, "shock_prob": 0.05, "shock_mag": (-2.0, 1.0)},
    "Experience and Track Record":              {"persistence": 0.96, "drift_std": 0.15, "shock_prob": 0.02, "shock_mag": (-1.0, 1.5)},
    "Financial Stability":                      {"persistence": 0.93, "drift_std": 0.22, "shock_prob": 0.04, "shock_mag": (-2.5, 1.0)},
    "Flexibility":                              {"persistence": 0.87, "drift_std": 0.35, "shock_prob": 0.05, "shock_mag": (-1.5, 1.5)},
    "Systems Integration":                      {"persistence": 0.95, "drift_std": 0.18, "shock_prob": 0.02, "shock_mag": (-0.5, 2.0)},
    "Technical Capability / Process Capability": {"persistence": 0.93, "drift_std": 0.20, "shock_prob": 0.03, "shock_mag": (-1.0, 2.0)},
    # ── Buyer criteria ──────────────────────────────────────────────────
    "Compliance & Regulatory Standards":        {"persistence": 0.94, "drift_std": 0.18, "shock_prob": 0.03, "shock_mag": (-1.5, 2.0)},
    "Demand Stability & Predictability":        {"persistence": 0.88, "drift_std": 0.32, "shock_prob": 0.06, "shock_mag": (-2.0, 1.5)},
    "Financial Stability & Creditworthiness":   {"persistence": 0.93, "drift_std": 0.22, "shock_prob": 0.04, "shock_mag": (-2.5, 1.0)},
    "Long-Term Strategic Value":                {"persistence": 0.95, "drift_std": 0.15, "shock_prob": 0.02, "shock_mag": (-1.0, 1.5)},
    "Market Reputation & Brand Impact":         {"persistence": 0.96, "drift_std": 0.12, "shock_prob": 0.02, "shock_mag": (-1.5, 1.0)},
    "Order Volume & Growth Potential":          {"persistence": 0.86, "drift_std": 0.35, "shock_prob": 0.07, "shock_mag": (-2.0, 2.0)},
    "Payment Performance":                      {"persistence": 0.91, "drift_std": 0.25, "shock_prob": 0.05, "shock_mag": (-2.0, 1.0)},
    "Responsiveness & Collaboration":           {"persistence": 0.89, "drift_std": 0.28, "shock_prob": 0.04, "shock_mag": (-1.5, 1.5)},
    "Technical Sophistication (Systems)":       {"persistence": 0.95, "drift_std": 0.18, "shock_prob": 0.02, "shock_mag": (-0.5, 2.0)},
}

# Shock event types for the event log
HARM_EVENTS: set[str] = {"quality_incident", "financial_downturn", "supply_disruption", "regulatory_penalty"}
BENE_EVENTS: set[str] = {"market_expansion", "technology_upgrade", "capacity_expansion", "new_certification"}
NEUT_EVENTS: set[str] = {"merger_acquisition", "management_change"}
SHOCK_EVENT_TYPES: list[str] = sorted(HARM_EVENTS | BENE_EVENTS | NEUT_EVENTS)

# Quarterly seasonal multipliers (index 0 = Q1, index 3 = Q4)
# Values are additive adjustments to the base score for that quarter.
SEASONAL_PATTERNS: dict[str, list[float]] = {
    "Q4_peak":        [-0.05, -0.02,  0.00, +0.15],
    "Q3_Q4_peak":     [-0.05,  0.00, +0.10, +0.12],
    "Q1_Q3_peak":     [+0.08, -0.03, +0.08, -0.05],
    "Q1_Q2_peak":     [+0.10, +0.08, -0.03, -0.05],
    "flat":           [ 0.00,  0.00,  0.00,  0.00],
}

# Criteria affected by seasonality (only these get seasonal adjustments)
SEASONAL_CRITERIA: dict[str, list[str]] = {
    "supplier": [
        "Delivery Performance",
        "Flexibility",
        "Cost / Price Competitiveness",
    ],
    "buyer": [
        "Order Volume & Growth Potential",
        "Demand Stability & Predictability",
        "Responsiveness & Collaboration",
    ],
}

# Map industry seasonal_peak_quarters → seasonal_pattern key
def get_seasonal_pattern(peak_quarters: list[int]) -> str:
    """Resolve an industry's peak-quarter list to a seasonal pattern key."""
    if not peak_quarters:
        return "flat"
    pq = sorted(peak_quarters)
    if pq == [4]:
        return "Q4_peak"
    if pq == [3, 4]:
        return "Q3_Q4_peak"
    if pq == [1, 3]:
        return "Q1_Q3_peak"
    if pq == [1, 2]:
        return "Q1_Q2_peak"
    return "flat"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11 · MATCHING & RELATIONSHIP PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# Average number of supplier relationships per buyer, by company size
AVG_RELATIONSHIPS_PER_BUYER: dict[str, tuple[int, int]] = {
    "Small":      (3, 8),
    "Medium":     (5, 15),
    "Large":      (10, 25),
    "Enterprise": (20, 50),
}

# Probability distribution over relationship quality levels
RELATIONSHIP_QUALITY_DISTRIBUTION: dict[str, float] = {
    "Excellent":   0.18,
    "Acceptable":  0.45,
    "Weak":        0.20,
    "Failed":      0.10,
    "Terminated":  0.07,
}

# Geographic compatibility bonus (same region = higher match probability)
GEO_SAME_REGION_BONUS: float = 0.15
GEO_ADJACENT_REGION_BONUS: float = 0.05

# Size compatibility preferences (buyer_size → preferred supplier_sizes)
SIZE_COMPATIBILITY: dict[str, list[str]] = {
    "Small":      ["Small", "Medium"],
    "Medium":     ["Small", "Medium", "Large"],
    "Large":      ["Medium", "Large", "Enterprise"],
    "Enterprise": ["Large", "Enterprise"],
}

# Minimum compatibility score to form a relationship (0–1)
MIN_COMPATIBILITY_THRESHOLD: float = 0.35


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12 · COMPANY NAME GENERATION
#
# Prefixes and suffixes used by the company factory to create realistic names.
# ═══════════════════════════════════════════════════════════════════════════════

COMPANY_NAME_PREFIXES: list[str] = [
    "Apex", "Atlas", "Beacon", "Blue Ridge", "Caliber", "Cascade", "Centurion",
    "Clearwater", "Continental", "Crestline", "Crown", "Delta", "Diamond",
    "Eagle", "Eastern", "Eclipse", "Elite", "Emerald", "Endeavor", "Equinox",
    "Evergreen", "Excel", "Falcon", "FirstLine", "Frontier", "Genesis",
    "Global", "Golden", "Grand", "Guardian", "Harmony", "Harvest", "Horizon",
    "Imperial", "Infinity", "Integral", "Iron Bridge", "Keystone", "Landmark",
    "Liberty", "Lighthouse", "Magellan", "Maple", "Meridian", "Metro",
    "Monarch", "Nexus", "Noble", "Nordic", "Northstar", "Nova", "Omega",
    "Onyx", "Pacific", "Paragon", "Peak", "Phoenix", "Pinnacle", "Pioneer",
    "Polaris", "Precision", "Premier", "Prism", "ProTech", "Quantum",
    "Radiant", "Raven", "Redwood", "Regent", "Reliance", "Resolute", "Ridge",
    "Riverstone", "Rocky Mountain", "Royal", "Sapphire", "Sentinel", "Sierra",
    "Silver", "Skyline", "Solaris", "Sovereign", "Spectrum", "Sterling",
    "Summit", "Synergy", "Titan", "Trident", "Trinity", "United", "Vanguard",
    "Velocity", "Vertex", "Vista", "Zenith",
]

COMPANY_NAME_SUFFIXES: dict[str, list[str]] = {
    "supplier": [
        "Industries", "Manufacturing", "Solutions", "Components", "Systems",
        "Materials", "Technologies", "Products", "Fabrication", "Engineering",
        "Supply Co.", "Works", "Production", "Enterprises", "Technical",
    ],
    "buyer": [
        "Corporation", "Group", "Holdings", "Enterprises", "International",
        "Global", "Partners", "Limited", "Inc.", "Company", "Co.",
        "Brands", "Retail", "Distribution", "Ventures",
    ],
}

COMPANY_NAME_LEGAL_FORMS: list[str] = [
    "Ltd.", "GmbH", "S.A.", "Corp.", "Inc.", "LLC", "AG", "B.V.",
    "Pty Ltd.", "S.r.l.", "Co., Ltd.", "PLC",
]
