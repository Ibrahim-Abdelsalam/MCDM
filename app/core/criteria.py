"""Fixed criteria definitions for supplier and buyer evaluation."""

from __future__ import annotations

from typing import ClassVar


class CriteriaConfig:
    """Store the fixed MCDM criteria for supplier and buyer evaluation."""

    SUPPLIER_CRITERIA: ClassVar[dict[str, dict[str, object]]] = {
        "Quality Performance": {"type": "benefit", "range": [1, 10]},
        "Delivery Performance": {"type": "benefit", "range": [1, 10]},
        "Cost Competitiveness": {"type": "cost", "range": [1, 10]},
        "Financial Stability": {"type": "benefit", "range": [1, 10]},
        "Technical Capability": {"type": "benefit", "range": [1, 10]},
        "Compliance & Sustainability": {"type": "benefit", "range": [1, 10]},
        "Systems Integration": {"type": "benefit", "range": [1, 10]},
        "Flexibility": {"type": "benefit", "range": [1, 10]},
        "Experience & Track Record": {"type": "benefit", "range": [1, 10]},
    }

    BUYER_CRITERIA: ClassVar[dict[str, dict[str, object]]] = {
        "Financial Stability & Creditworthiness": {"type": "benefit", "range": [1, 10]},
        "Payment Performance": {"type": "benefit", "range": [1, 10]},
        "Order Volume & Growth Potential": {"type": "benefit", "range": [1, 10]},
        "Demand Stability & Predictability": {"type": "benefit", "range": [1, 10]},
        "Responsiveness & Collaboration": {"type": "benefit", "range": [1, 10]},
        "Compliance & Regulatory Standards": {"type": "benefit", "range": [1, 10]},
        "Technical Sophistication & Systems Integration": {"type": "benefit", "range": [1, 10]},
        "Market Reputation & Brand Impact": {"type": "benefit", "range": [1, 10]},
        "Long-Term Strategic Value": {"type": "benefit", "range": [1, 10]},
    }

    @classmethod
    def get_criteria_names(cls, entity_type: str) -> list[str]:
        """Return the ordered criterion names for the requested entity type."""
        normalized_entity_type = entity_type.strip().lower()
        if normalized_entity_type == "supplier":
            return list(cls.SUPPLIER_CRITERIA.keys())
        if normalized_entity_type == "buyer":
            return list(cls.BUYER_CRITERIA.keys())
        raise ValueError("entity_type must be either 'supplier' or 'buyer'.")
