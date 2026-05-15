"""AHP (Analytical Hierarchy Process) MCDM solver."""

from __future__ import annotations

import pandas as pd

from .criteria import CriteriaConfig
from .normalizer import Normalizer


class AHPSolver:
    """Solve using AHP method: weighted sum of normalized scores."""

    def __init__(self) -> None:
        """Initialize the AHP solver."""

    def solve(
        self,
        weight_vector: dict[str, float],
        scores_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Solve using AHP: weighted average of normalized scores.
        
        Args:
            weight_vector: dict mapping criterion names to normalized weights
            scores_df: DataFrame with ID column and criterion score columns
        
        Returns:
            DataFrame with columns: [ID, AHP_Score, AHP_Rank]
        """
        result = scores_df[["ID"]].copy()

        # Ensure weights sum to 1
        weight_sum = sum(weight_vector.values())
        normalized_weights = {k: v / weight_sum for k, v in weight_vector.items()}

        # Min-max normalize the score columns before weighting
        normalized_scores_df = Normalizer.minmax_normalize(scores_df, CriteriaConfig)

        ahp_scores = []
        for _, row in normalized_scores_df.iterrows():
            score = 0.0
            for criterion_name, weight in normalized_weights.items():
                if criterion_name in normalized_scores_df.columns:
                    criterion_value = float(row[criterion_name])
                    score += weight * criterion_value
            ahp_scores.append(score)

        result["AHP_Score"] = ahp_scores
        result["AHP_Rank"] = result["AHP_Score"].rank(method="min", ascending=False).astype(int)
        
        return result.sort_values("AHP_Rank")
