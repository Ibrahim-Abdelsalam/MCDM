"""Data normalization utilities for MCDM analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .criteria import CriteriaConfig


class Normalizer:
    """Normalize scores using various normalization strategies."""

    @staticmethod
    def vector_normalize(df: pd.DataFrame, criteria_config: CriteriaConfig) -> pd.DataFrame:
        """Normalize scores using vector normalization (Euclidean norm)."""
        result = df.copy()
        criteria_names = list(CriteriaConfig.SUPPLIER_CRITERIA.keys()) + list(CriteriaConfig.BUYER_CRITERIA.keys())

        for criterion_name in criteria_names:
            if criterion_name not in result.columns:
                continue
            col_values = result[criterion_name].to_numpy(dtype=float)
            col_norm = np.sqrt(np.sum(col_values**2))
            if col_norm > 1e-10:
                result[criterion_name] = col_values / col_norm
            else:
                result[criterion_name] = 0.0
        return result

    @staticmethod
    def minmax_normalize(df: pd.DataFrame, criteria_config: CriteriaConfig) -> pd.DataFrame:
        """Normalize scores using min-max normalization, respecting benefit/cost types."""
        result = df.copy()
        all_criteria = {
            **CriteriaConfig.SUPPLIER_CRITERIA,
            **CriteriaConfig.BUYER_CRITERIA,
        }

        for criterion_name, criterion_info in all_criteria.items():
            if criterion_name not in result.columns:
                continue

            col_values = result[criterion_name].to_numpy(dtype=float)
            col_min = float(np.min(col_values))
            col_max = float(np.max(col_values))
            criterion_type = criterion_info.get("type", "benefit")

            if abs(col_max - col_min) <= 1e-10:
                result[criterion_name] = 0.5
            elif criterion_type == "cost":
                result[criterion_name] = (col_max - col_values) / (col_max - col_min)
            else:
                result[criterion_name] = (col_values - col_min) / (col_max - col_min)

        return result
