"""VIKOR (VlseKriterijumska Optimizacija I Kompromisno Resenje) MCDM solver."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .criteria import CriteriaConfig


class VIKORSolver:
    """Solve using VIKOR method with configurable v parameter."""

    def __init__(self) -> None:
        """Initialize the VIKOR solver."""

    def solve(
        self,
        weight_vector: dict[str, float],
        scores_df: pd.DataFrame,
        v: float = 0.5,
    ) -> pd.DataFrame:
        """
        Solve using VIKOR: compromise ranking based on group utility and regret.
        
        Args:
            weight_vector: dict mapping criterion names to normalized weights
            scores_df: DataFrame with ID column and criterion score columns
            v: weight of group utility (0 ≤ v ≤ 1, default 0.5)
        
        Returns:
            DataFrame with columns: [ID, VIKOR_Score, VIKOR_Rank]
        """
        if not 0.0 <= v <= 1.0:
            raise ValueError("v must be between 0.0 and 1.0.")
        
        # Ensure weights sum to 1
        weight_sum = sum(weight_vector.values())
        normalized_weights = {k: v / weight_sum for k, v in weight_vector.items()}
        
        # Get all criteria info
        all_criteria = {
            **CriteriaConfig.SUPPLIER_CRITERIA,
            **CriteriaConfig.BUYER_CRITERIA,
        }
        
        # Prepare criterion names and data
        criteria_names = [name for name in weight_vector.keys() if name in scores_df.columns]
        raw_data = scores_df[criteria_names].to_numpy(dtype=float)
        
        # Min-max normalization: track best and worst per criterion
        best_f = np.zeros(len(criteria_names))
        worst_f = np.zeros(len(criteria_names))
        normalized_data = np.zeros_like(raw_data)
        
        for j, criterion_name in enumerate(criteria_names):
            criterion_type = all_criteria.get(criterion_name, {}).get("type", "benefit")
            col_min = np.min(raw_data[:, j])
            col_max = np.max(raw_data[:, j])
            
            if criterion_type == "benefit":
                best_f[j] = col_max
                worst_f[j] = col_min
            else:  # cost
                best_f[j] = col_min
                worst_f[j] = col_max
            
            # Min-max normalize
            if abs(col_max - col_min) > 1e-10:
                if criterion_type == "benefit":
                    normalized_data[:, j] = (raw_data[:, j] - col_min) / (col_max - col_min)
                else:
                    normalized_data[:, j] = (col_max - raw_data[:, j]) / (col_max - col_min)
            else:
                normalized_data[:, j] = 0.5
        
        # Calculate d_ij = w_j × (f*_j - x_ij) / (f*_j - f-_j)
        d_matrix = np.zeros_like(normalized_data)
        for j, criterion_name in enumerate(criteria_names):
            weight = normalized_weights.get(criterion_name, 1.0)
            denominator = abs(best_f[j] - worst_f[j]) if abs(best_f[j] - worst_f[j]) > 1e-10 else 1e-10
            for i in range(len(raw_data)):
                d_matrix[i, j] = weight * abs(best_f[j] - raw_data[i, j]) / denominator
        
        # Calculate S_i (group utility) and R_i (individual regret)
        s_scores = np.sum(d_matrix, axis=1)
        r_scores = np.max(d_matrix, axis=1)
        
        # Determine S* (best), S- (worst), R* (best), R- (worst)
        s_min = np.min(s_scores)
        s_max = np.max(s_scores)
        r_min = np.min(r_scores)
        r_max = np.max(r_scores)
        
        # Calculate Q_i
        s_denom = s_max - s_min if abs(s_max - s_min) > 1e-10 else 1e-10
        r_denom = r_max - r_min if abs(r_max - r_min) > 1e-10 else 1e-10
        
        q_scores = (
            v * (s_scores - s_min) / s_denom +
            (1 - v) * (r_scores - r_min) / r_denom
        )
        
        # Determine compromise solution
        sorted_indices = np.argsort(q_scores)
        is_compromise = np.zeros(len(q_scores), dtype=bool)
        
        if len(q_scores) > 0:
            best_idx = sorted_indices[0]
            
            # Condition 1: Acceptable Advantage (Q(a'') - Q(a') >= DQ)
            dq = 1.0 / (len(q_scores) - 1) if len(q_scores) > 1 else 0.0
            cond1_passed = False
            if len(q_scores) > 1:
                second_best_idx = sorted_indices[1]
                if (q_scores[second_best_idx] - q_scores[best_idx]) >= dq:
                    cond1_passed = True
            else:
                cond1_passed = True
                
            # Condition 2: Acceptable Stability (Top Q is also Top S or Top R)
            best_s_indices = np.where(s_scores == np.min(s_scores))[0]
            best_r_indices = np.where(r_scores == np.min(r_scores))[0]
            cond2_passed = (best_idx in best_s_indices) or (best_idx in best_r_indices)
            
            if cond1_passed and cond2_passed:
                is_compromise[best_idx] = True
            elif cond1_passed and not cond2_passed:
                is_compromise[best_idx] = True
                if len(q_scores) > 1:
                    is_compromise[sorted_indices[1]] = True
            elif not cond1_passed:
                # Include alternatives a', a'', ..., a(m) where Q(a(m)) - Q(a') < DQ
                is_compromise[best_idx] = True
                for i in range(1, len(q_scores)):
                    idx = sorted_indices[i]
                    if (q_scores[idx] - q_scores[best_idx]) < dq:
                        is_compromise[idx] = True
                    else:
                        break

        # Invert scores so higher = better (consistent with AHP/TOPSIS)
        final_scores = 1.0 - q_scores
        
        result = scores_df[["ID"]].copy()
        result["VIKOR_Score"] = final_scores
        result["VIKOR_Rank"] = result["VIKOR_Score"].rank(method="min", ascending=False).astype(int)
        result["Is_Compromise"] = is_compromise
        
        return result.sort_values("VIKOR_Rank")
