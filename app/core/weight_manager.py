"""Weight scheme persistence and normalization utilities."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..config import BASE_DIR
from .criteria import CriteriaConfig


class WeightSchemeManager:
    """Manage weight schemes stored as JSON files per entity type."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the manager with the application data directory."""
        self.data_dir = data_dir or (BASE_DIR / "data")

    def _normalize_entity_type(self, entity_type: str) -> str:
        """Normalize and validate an entity type value."""
        normalized_entity_type = entity_type.strip().lower()
        if normalized_entity_type not in {"supplier", "buyer"}:
            raise ValueError("entity_type must be either 'supplier' or 'buyer'.")
        return normalized_entity_type

    def _criteria_names(self, entity_type: str) -> list[str]:
        """Return the ordered criteria names for an entity type."""
        return CriteriaConfig.get_criteria_names(entity_type)

    def _weights_directory(self, entity_type: str) -> Path:
        """Return the directory that stores weight scheme JSON files."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        return self.data_dir / normalized_entity_type / "weights"

    def _safe_filename(self, scheme_name: str) -> str:
        """Create a stable filename fragment for a scheme name."""
        cleaned_name = re.sub(r"[^A-Za-z0-9]+", "_", scheme_name.strip()).strip("_")
        if not cleaned_name:
            raise ValueError("scheme_name cannot be empty.")
        return cleaned_name.lower()

    def _scheme_path(self, entity_type: str, scheme_name: str) -> Path:
        """Build the JSON file path for a weight scheme."""
        return self._weights_directory(entity_type) / f"{self._safe_filename(scheme_name)}.json"

    def _ensure_directory(self, entity_type: str) -> Path:
        """Create the weights directory if needed and return it."""
        directory = self._weights_directory(entity_type)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _load_scheme_file(self, path: Path) -> dict[str, Any]:
        """Load one scheme record from disk."""
        try:
            with path.open("r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except OSError as exc:
            raise OSError(f"Failed to read weight scheme file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in weight scheme file: {path}") from exc

    def _find_scheme_file(self, entity_type: str, scheme_name: str) -> Path | None:
        """Find a scheme file by exact stored scheme name or filename."""
        directory = self._weights_directory(entity_type)
        if not directory.exists():
            return None

        target_name = scheme_name.strip().lower()
        filename_match = self._scheme_path(entity_type, scheme_name)
        if filename_match.exists():
            return filename_match

        for path in directory.glob("*.json"):
            record = self._load_scheme_file(path)
            stored_name = str(record.get("scheme_name", "")).strip().lower()
            if stored_name == target_name:
                return path
        return None

    def _validate_weights(self, entity_type: str, weights_dict: dict[str, Any]) -> None:
        """Validate that the provided weights cover the full criteria set."""
        criteria_names = self._criteria_names(entity_type)
        if set(weights_dict.keys()) != set(criteria_names):
            missing = [name for name in criteria_names if name not in weights_dict]
            extra = [name for name in weights_dict if name not in criteria_names]
            messages: list[str] = []
            if missing:
                messages.append(f"missing criteria: {', '.join(missing)}")
            if extra:
                messages.append(f"unexpected criteria: {', '.join(extra)}")
            raise ValueError("weights_dict must contain exactly one complete criteria set (" + "; ".join(messages) + ").")

        for criterion_name, weight_value in weights_dict.items():
            if not isinstance(weight_value, (int, float)):
                raise ValueError(f"Weight for '{criterion_name}' must be numeric.")
            if weight_value < 0:
                raise ValueError(f"Weight for '{criterion_name}' must be non-negative.")

    def save_scheme(self, entity_type: str, scheme_name: str, weights_dict: dict[str, Any]) -> Path:
        """Save a raw weight scheme as JSON for the requested entity type."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        self._validate_weights(normalized_entity_type, weights_dict)

        record = {
            "scheme_name": scheme_name.strip(),
            "entity_type": normalized_entity_type,
            "weights": {criterion: weights_dict[criterion] for criterion in self._criteria_names(normalized_entity_type)},
        }

        self._ensure_directory(normalized_entity_type)
        scheme_path = self._scheme_path(normalized_entity_type, scheme_name)

        try:
            with scheme_path.open("w", encoding="utf-8") as file_handle:
                json.dump(record, file_handle, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise OSError(f"Failed to save weight scheme file: {scheme_path}") from exc

        return scheme_path

    def load_scheme(self, entity_type: str, scheme_name: str) -> dict[str, float]:
        """Load and normalize a saved weight scheme."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        scheme_path = self._find_scheme_file(normalized_entity_type, scheme_name)
        if scheme_path is None:
            raise FileNotFoundError(
                f"Weight scheme '{scheme_name}' was not found for entity type '{normalized_entity_type}'."
            )

        record = self._load_scheme_file(scheme_path)
        raw_weights = record.get("weights", {})
        self._validate_weights(normalized_entity_type, raw_weights)

        weight_total = float(sum(float(value) for value in raw_weights.values()))
        if abs(weight_total) <= 1e-10:
            raise ValueError("Weight scheme cannot be normalized because the sum of weights is zero.")

        return {
            criterion: float(raw_weights[criterion]) / weight_total
            for criterion in self._criteria_names(normalized_entity_type)
        }

    def list_schemes(self, entity_type: str) -> list[str]:
        """List scheme names stored for an entity type."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        directory = self._weights_directory(normalized_entity_type)
        if not directory.exists():
            return []

        scheme_names: list[str] = []
        for path in sorted(directory.glob("*.json")):
            record = self._load_scheme_file(path)
            scheme_name = str(record.get("scheme_name", "")).strip()
            if scheme_name:
                scheme_names.append(scheme_name)
        return scheme_names

    def delete_scheme(self, entity_type: str, scheme_name: str) -> None:
        """Delete a stored weight scheme."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        scheme_path = self._find_scheme_file(normalized_entity_type, scheme_name)
        if scheme_path is None:
            raise FileNotFoundError(
                f"Weight scheme '{scheme_name}' was not found for entity type '{normalized_entity_type}'."
            )

        try:
            scheme_path.unlink()
        except OSError as exc:
            raise OSError(f"Failed to delete weight scheme file: {scheme_path}") from exc
