"""Company persistence and tabular loading utilities."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import BASE_DIR, SCORE_MAX, SCORE_MIN
from .criteria import CriteriaConfig


class CompanyManager:
    """Manage company records stored as JSON files per entity type."""

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

    def _company_directory(self, entity_type: str) -> Path:
        """Return the directory that stores company JSON files."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        return self.data_dir / normalized_entity_type / "companies"

    def _safe_filename(self, company_name: str) -> str:
        """Create a stable filename fragment for a company name."""
        cleaned_name = re.sub(r"[^A-Za-z0-9]+", "_", company_name.strip()).strip("_")
        if not cleaned_name:
            raise ValueError("company_name cannot be empty.")
        return cleaned_name.lower()

    def _company_path(self, entity_type: str, company_name: str) -> Path:
        """Build the JSON file path for a company record."""
        return self._company_directory(entity_type) / f"{self._safe_filename(company_name)}.json"

    def _ensure_directory(self, entity_type: str) -> Path:
        """Create the company directory if needed and return it."""
        directory = self._company_directory(entity_type)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def _load_company_file(self, path: Path) -> dict[str, Any]:
        """Load one company record from disk."""
        try:
            with path.open("r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except OSError as exc:
            raise OSError(f"Failed to read company file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in company file: {path}") from exc

    def _find_company_file(self, entity_type: str, company_name: str) -> Path | None:
        """Find a company file by exact stored company name or filename."""
        directory = self._company_directory(entity_type)
        if not directory.exists():
            return None

        target_name = company_name.strip().lower()
        filename_match = self._company_path(entity_type, company_name)
        if filename_match.exists():
            return filename_match

        for path in directory.glob("*.json"):
            record = self._load_company_file(path)
            stored_name = str(record.get("company_name", "")).strip().lower()
            if stored_name == target_name:
                return path
        return None

    def validate_scores(self, scores_dict: dict[str, Any]) -> None:
        """Validate that scores match one complete criteria set in range."""
        score_keys = set(scores_dict.keys())
        criteria_sets = [CriteriaConfig.SUPPLIER_CRITERIA, CriteriaConfig.BUYER_CRITERIA]

        for criteria in criteria_sets:
            criteria_names = set(criteria.keys())
            if score_keys == criteria_names:
                break
        else:
            raise ValueError("scores_dict must contain exactly one complete criteria set.")

        for criterion_name, score_value in scores_dict.items():
            if not isinstance(score_value, (int, float)):
                raise ValueError(f"Score for '{criterion_name}' must be numeric.")
            if score_value < SCORE_MIN or score_value > SCORE_MAX:
                raise ValueError(
                    f"Score for '{criterion_name}' must be between {SCORE_MIN} and {SCORE_MAX}."
                )

    def add_company(self, entity_type: str, company_name: str, scores_dict: dict[str, Any]) -> Path:
        """Save a company record as JSON for the requested entity type."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        self.validate_scores(scores_dict)

        criteria_names = self._criteria_names(normalized_entity_type)
        missing_criteria = [name for name in criteria_names if name not in scores_dict]
        if missing_criteria:
            raise ValueError(f"Missing criteria scores: {', '.join(missing_criteria)}")

        record = {
            "company_name": company_name.strip(),
            "entity_type": normalized_entity_type,
            "scores": {criterion: scores_dict[criterion] for criterion in criteria_names},
        }

        self._ensure_directory(normalized_entity_type)
        company_path = self._company_path(normalized_entity_type, company_name)

        try:
            with company_path.open("w", encoding="utf-8") as file_handle:
                json.dump(record, file_handle, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise OSError(f"Failed to save company file: {company_path}") from exc

        return company_path

    def remove_company(self, entity_type: str, company_name: str) -> None:
        """Delete a stored company record."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        company_path = self._find_company_file(normalized_entity_type, company_name)
        if company_path is None:
            raise FileNotFoundError(
                f"Company '{company_name}' was not found for entity type '{normalized_entity_type}'."
            )

        try:
            company_path.unlink()
        except OSError as exc:
            raise OSError(f"Failed to remove company file: {company_path}") from exc

    def list_companies(self, entity_type: str) -> list[str]:
        """List company names stored for an entity type."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        directory = self._company_directory(normalized_entity_type)
        if not directory.exists():
            return []

        company_names: list[str] = []
        for path in sorted(directory.glob("*.json")):
            record = self._load_company_file(path)
            company_name = str(record.get("company_name", "")).strip()
            if company_name:
                company_names.append(company_name)
        return company_names

    def load_all_as_dataframe(self, entity_type: str) -> pd.DataFrame:
        """Load all company records for an entity type into a DataFrame."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        criteria_names = self._criteria_names(normalized_entity_type)
        directory = self._company_directory(normalized_entity_type)

        rows: list[dict[str, Any]] = []
        if directory.exists():
            for path in sorted(directory.glob("*.json")):
                record = self._load_company_file(path)
                scores = record.get("scores", {})
                row = {"ID": str(record.get("company_name", path.stem))}
                row.update({criterion: scores.get(criterion) for criterion in criteria_names})
                rows.append(row)

        columns = ["ID", *criteria_names]
        return pd.DataFrame(rows, columns=columns)
