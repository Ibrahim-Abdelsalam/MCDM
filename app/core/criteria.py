"""Dynamic criteria definitions for supplier and buyer evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

# Define path for criteria storage
DATA_DIR = Path(__file__).parent.parent / "data"
CRITERIA_FILE = DATA_DIR / "criteria.json"


class CriteriaConfig:
    """Store and manage dynamic MCDM criteria for supplier and buyer evaluation."""

    # Default Baseline as per requirements
    _DEFAULT_CRITERIA: ClassVar[dict[str, dict[str, dict[str, object]]]] = {
        "supplier": {
            "Quality Performance": {"type": "benefit", "range": [1, 10]},
            "Delivery Performance": {"type": "benefit", "range": [1, 10]},
            "Cost Competitiveness": {"type": "cost", "range": [1, 10]},
        },
        "buyer": {
            "Order Volume and Growth Potential": {"type": "benefit", "range": [1, 10]},
            "Demand Stability and Predictability": {"type": "benefit", "range": [1, 10]},
            "Responsiveness and Collaboration": {"type": "benefit", "range": [1, 10]},
        }
    }

    _criteria_cache: ClassVar[dict[str, dict[str, dict[str, object]]] | None] = None

    @classmethod
    def _load_criteria(cls) -> dict[str, dict[str, dict[str, object]]]:
        if cls._criteria_cache is not None:
            return cls._criteria_cache

        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)

        if CRITERIA_FILE.exists():
            try:
                with open(CRITERIA_FILE, "r", encoding="utf-8") as f:
                    cls._criteria_cache = json.load(f)
                    return cls._criteria_cache
            except Exception:
                pass # Fallback to default if file is corrupted

        # If we reached here, initialize defaults
        cls._criteria_cache = {
            "supplier": dict(cls._DEFAULT_CRITERIA["supplier"]),
            "buyer": dict(cls._DEFAULT_CRITERIA["buyer"])
        }
        cls._save_criteria()
        return cls._criteria_cache

    @classmethod
    def _save_criteria(cls) -> None:
        if cls._criteria_cache is None:
            return
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CRITERIA_FILE, "w", encoding="utf-8") as f:
            json.dump(cls._criteria_cache, f, indent=4)

    @classmethod
    def get_all_criteria(cls, entity_type: str) -> dict[str, dict[str, object]]:
        """Return the dictionary of criteria for the requested entity type."""
        data = cls._load_criteria()
        normalized_entity_type = entity_type.strip().lower()
        if normalized_entity_type in data:
            return data[normalized_entity_type]
        raise ValueError("entity_type must be either 'supplier' or 'buyer'.")

    @classmethod
    def get_criteria_names(cls, entity_type: str) -> list[str]:
        """Return the ordered criterion names for the requested entity type."""
        return list(cls.get_all_criteria(entity_type).keys())

    @classmethod
    def add_criterion(cls, entity_type: str, name: str, crit_type: str = "benefit") -> None:
        data = cls._load_criteria()
        normalized = entity_type.strip().lower()
        if normalized not in data:
            raise ValueError("Invalid entity type")
        if name in data[normalized]:
            raise ValueError(f"Criterion '{name}' already exists.")
        
        data[normalized][name] = {"type": crit_type, "range": [1, 10]}
        cls._save_criteria()

    @classmethod
    def update_criterion(cls, entity_type: str, old_name: str, new_name: str, crit_type: str) -> None:
        data = cls._load_criteria()
        normalized = entity_type.strip().lower()
        if normalized not in data:
            raise ValueError("Invalid entity type")
        if old_name not in data[normalized]:
            raise ValueError(f"Criterion '{old_name}' not found.")
        
        # We need to preserve order, so we recreate the dict
        new_dict = {}
        for k, v in data[normalized].items():
            if k == old_name:
                new_dict[new_name] = {"type": crit_type, "range": [1, 10]}
            else:
                new_dict[k] = v
        data[normalized] = new_dict
        cls._save_criteria()

    @classmethod
    def delete_criterion(cls, entity_type: str, name: str) -> None:
        data = cls._load_criteria()
        normalized = entity_type.strip().lower()
        if normalized not in data:
            raise ValueError("Invalid entity type")
        if name in data[normalized]:
            del data[normalized][name]
            cls._save_criteria()

    @classmethod
    def clear_cache(cls) -> None:
        """Force a reload from disk next time criteria are requested."""
        cls._criteria_cache = None
