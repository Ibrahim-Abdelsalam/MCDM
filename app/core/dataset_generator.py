"""Synthetic dataset generation utilities for testing analyses."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import BASE_DIR, SCORE_MAX, SCORE_MIN
from .criteria import CriteriaConfig


class DatasetGenerator:
    """Generate synthetic supplier or buyer datasets for analysis."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the generator with the application data directory."""
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

    def _dataset_directory(self, entity_type: str) -> Path:
        """Return the directory that stores generated datasets."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        return self.data_dir / normalized_entity_type / "datasets"

    def _dataset_path(self, entity_type: str) -> Path:
        """Return the CSV path for a generated dataset."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        return self._dataset_directory(normalized_entity_type) / f"{normalized_entity_type}_dataset.csv"

    def _entity_prefix(self, entity_type: str) -> str:
        """Return the ID prefix for an entity type."""
        normalized_entity_type = self._normalize_entity_type(entity_type)
        return "SUP" if normalized_entity_type == "supplier" else "BUY"

    def generate(self, entity_type: str, n: int, seed: int | None = None) -> pd.DataFrame:
        """Generate a synthetic dataset, save it to CSV, and return it as a DataFrame."""
        if not isinstance(n, int):
            raise TypeError("n must be an integer.")
        if n < 10 or n > 10000:
            raise ValueError("n must be between 10 and 10000.")

        normalized_entity_type = self._normalize_entity_type(entity_type)
        criteria_names = self._criteria_names(normalized_entity_type)
        rng = np.random.default_rng(seed)

        rows: list[dict[str, float | str]] = []
        prefix = self._entity_prefix(normalized_entity_type)
        for index in range(1, n + 1):
            row: dict[str, float | str] = {"ID": f"{prefix}-{index:03d}"}
            for criterion_name in criteria_names:
                score_value = float(rng.uniform(SCORE_MIN, SCORE_MAX))
                row[criterion_name] = round(score_value, 2)
            rows.append(row)

        dataset = pd.DataFrame(rows, columns=["ID", *criteria_names])

        dataset_directory = self._dataset_directory(normalized_entity_type)
        dataset_directory.mkdir(parents=True, exist_ok=True)
        dataset_path = self._dataset_path(normalized_entity_type)

        try:
            dataset.to_csv(dataset_path, index=False)
        except OSError as exc:
            raise OSError(f"Failed to save generated dataset: {dataset_path}") from exc

        return dataset
