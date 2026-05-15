"""TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) MCDM solver."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .criteria import CriteriaConfig
from .normalizer import Normalizer


class TOPSISSolver:
    """Solve using TOPSIS method."""

    def __init__(self) -> None:
        """Initialize the TOPSIS solver."""

    def solve(
        self,
        weight_vector: dict[str, float],
        scores_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Solve using TOPSIS: distance to ideal and anti-ideal solutions.
        
        Args:
            weight_vector: dict mapping criterion names to normalized weights
            scores_df: DataFrame with ID column and criterion score columns
        
        Returns:
            DataFrame with columns: [ID, TOPSIS_Score, TOPSIS_Rank]
        """
        # Ensure weights sum to 1
        weight_sum = sum(weight_vector.values())
        normalized_weights = {k: v / weight_sum for k, v in weight_vector.items()}
        
        # Get all criteria info
        all_criteria = {
            **CriteriaConfig.SUPPLIER_CRITERIA,
            **CriteriaConfig.BUYER_CRITERIA,
        }
        
        # Vector normalization
        criteria_names = [name for name in weight_vector.keys() if name in scores_df.columns]
        criterion_data = scores_df[criteria_names].to_numpy(dtype=float)
        
        # Normalize: r_ij = x_ij / sqrt(Σ x_kj²)
        norm_factors = np.sqrt(np.sum(criterion_data**2, axis=0))
        normalized_data = np.zeros_like(criterion_data)
        for j, norm_factor in enumerate(norm_factors):
            if norm_factor > 1e-10:
                normalized_data[:, j] = criterion_data[:, j] / norm_factor
            else:
                normalized_data[:, j] = 0.0
        
        # Weighted matrix: v_ij = w_j × r_ij
        weighted_data = np.zeros_like(normalized_data)
        for j, criterion_name in enumerate(criteria_names):
            weight = normalized_weights.get(criterion_name, 1.0)
            weighted_data[:, j] = weight * normalized_data[:, j]
        
        # Determine ideal and anti-ideal solutions
        ideal = np.zeros(len(criteria_names))
        anti_ideal = np.zeros(len(criteria_names))
        
        for j, criterion_name in enumerate(criteria_names):
            criterion_type = all_criteria.get(criterion_name, {}).get("type", "benefit")
            if criterion_type == "benefit":
                ideal[j] = np.max(weighted_data[:, j])
                anti_ideal[j] = np.min(weighted_data[:, j])
            else:  # cost
                ideal[j] = np.min(weighted_data[:, j])
                anti_ideal[j] = np.max(weighted_data[:, j])
        
        # Calculate separation measures
        d_plus = np.sqrt(np.sum((weighted_data - ideal)**2, axis=1))
        d_minus = np.sqrt(np.sum((weighted_data - anti_ideal)**2, axis=1))
        
        # Calculate TOPSIS scores
        topsis_scores = d_minus / (d_plus + d_minus + 1e-10)
        
        result = scores_df[["ID"]].copy()
        result["TOPSIS_Score"] = topsis_scores
        result["TOPSIS_Rank"] = result["TOPSIS_Score"].rank(method="min", ascending=False).astype(int)
        
        return result.sort_values("TOPSIS_Rank")
