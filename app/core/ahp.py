"""Fuzzy AHP (FAHP) MCDM solver."""

from __future__ import annotations

import pandas as pd
import numpy as np


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

    def derive_weights(self, pairwise_df: pd.DataFrame) -> dict[str, float]:
        """
        Derive weights using Buckley's method.
        
        Args:
            pairwise_df: DataFrame containing a pairwise matrix in long format.
                         Columns: criterion_i, criterion_j, lower/middle/upper (or l/m/u)
                         Can be full matrix or upper-triangle only.
                         
        Returns:
            dict mapping criterion name to normalized crisp weight.
        """
        l_col = "l" if "l" in pairwise_df.columns else "lower"
        m_col = "m" if "m" in pairwise_df.columns else "middle"
        u_col = "u" if "u" in pairwise_df.columns else "upper"
        has_tfn = l_col in pairwise_df.columns and m_col in pairwise_df.columns and u_col in pairwise_df.columns
        
        crits = list(pd.concat([pairwise_df["criterion_i"], pairwise_df["criterion_j"]]).unique())
        n = len(crits)
        c_idx = {c: i for i, c in enumerate(crits)}
        
        A_l = np.ones((n, n))
        A_m = np.ones((n, n))
        A_u = np.ones((n, n))
        
        for _, row in pairwise_df.iterrows():
            i, j = c_idx[row["criterion_i"]], c_idx[row["criterion_j"]]
            if has_tfn:
                l_val, m_val, u_val = float(row[l_col]), float(row[m_col]), float(row[u_col])
            else:
                comp = float(row["comparison_value"])
                l_val, m_val, u_val = comp, comp, comp
                
            A_l[i, j] = l_val
            A_m[i, j] = m_val
            A_u[i, j] = u_val
            
            # Reciprocal reconstruction for lower triangle
            if i != j:
                A_l[j, i] = 1.0 / u_val
                A_m[j, i] = 1.0 / m_val
                A_u[j, i] = 1.0 / l_val
                
        r_l = np.prod(A_l, axis=1) ** (1.0 / n)
        r_m = np.prod(A_m, axis=1) ** (1.0 / n)
        r_u = np.prod(A_u, axis=1) ** (1.0 / n)
        
        R_l, R_m, R_u = np.sum(r_l), np.sum(r_m), np.sum(r_u)
        R_inv_l, R_inv_m, R_inv_u = 1.0 / R_u, 1.0 / R_m, 1.0 / R_l
        
        w_l = r_l * R_inv_l
        w_m = r_m * R_inv_m
        w_u = r_u * R_inv_u
        
        w_crisp = (w_l + w_m + w_u) / 3.0
        w_norm = w_crisp / np.sum(w_crisp)
        
        return {c: float(w_norm[i]) for i, c in enumerate(crits)}

