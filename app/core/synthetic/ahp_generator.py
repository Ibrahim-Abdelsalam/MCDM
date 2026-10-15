"""
AHP Generator.

Generates Decision-Maker Direct Weights, AHP Pairwise Comparison Matrices,
and calculates analytical eigenvectors & Consistency Ratios with repair logic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


class AHPGenerator:
    """Generates synthetic expert judgments for MCDM scenarios."""

    def __init__(self, seed: int = config.DEFAULT_SEED):
        self.rng = np.random.default_rng(seed)

    def _to_tfn(self, val: float) -> tuple[float, float, float]:
        """Projects a continuous ratio to the TFN linguistic scale."""
        if val >= 1.0:
            k = int(np.clip(round(val), 1, 6))
            if k == 1:
                return (1.0, 1.0, 1.0)
            else:
                return (float(k-1), float(k), float(k+1))
        else:
            inv_val = 1.0 / val
            k = int(np.clip(round(inv_val), 1, 6))
            if k == 1:
                return (1.0, 1.0, 1.0)
            else:
                return (1.0/float(k+1), 1.0/float(k), 1.0/float(k-1))

    def _compute_ahp_metrics(self, matrix: np.ndarray) -> tuple[np.ndarray, float, float, float]:
        """Calculates principal eigenvector, lambda_max, CI, and CR."""
        n = matrix.shape[0]
        
        # Perron-Frobenius theorem guarantees unique positive principal eigenvector
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_idx = np.argmax(np.real(eigenvalues))
        lambda_max = np.real(eigenvalues[max_idx])
        w = np.real(eigenvectors[:, max_idx])
        
        # Normalize
        if np.sum(w) < 0:
            w = -w
        w = w / np.sum(w)
        
        # Consistency Index and Ratio
        ci = (lambda_max - n) / (n - 1)
        ri = config.SAATY_RI.get(n, 1.45) # 1.45 is for n=9
        cr = ci / ri if ri > 0 else 0.0
        
        return w, lambda_max, ci, cr

    def _generate_pairwise_matrix(self, priority_vector: np.ndarray, target_cr_min: float, target_cr_max: float) -> dict:
        """
        Generates a reciprocal TFN matrix from a priority vector, adding noise 
        until the CR falls strictly within [target_cr_min, target_cr_max].
        """
        n = len(priority_vector)
        base_matrix = np.outer(priority_vector, 1.0 / priority_vector)
        
        repaired = False
        original_cr = None
        final_cr = None
        best_matrix_tfn = None
        best_matrix_defuzz = None
        
        noise_std = 0.1 + (target_cr_max * 1.5)
        
        for iteration in range(config.MAX_REPAIR_ITERATIONS):
            noise = np.exp(self.rng.normal(0, noise_std, size=(n, n)))
            matrix_tfn = [[(1.0, 1.0, 1.0) for _ in range(n)] for _ in range(n)]
            matrix_defuzz = np.zeros((n, n))
            
            for i in range(n):
                matrix_defuzz[i, i] = 1.0
                for j in range(i + 1, n):
                    l, m, u = self._to_tfn(base_matrix[i, j] * noise[i, j])
                    matrix_tfn[i][j] = (l, m, u)
                    matrix_tfn[j][i] = (1.0/u, 1.0/m, 1.0/l)
                    
                    matrix_defuzz[i, j] = (l + 2*m + u) / 4.0
                    matrix_defuzz[j, i] = (1.0/u + 2.0/m + 1.0/l) / 4.0
                    
            _, _, _, cr = self._compute_ahp_metrics(matrix_defuzz)
            
            if iteration == 0:
                original_cr = cr
                
            if target_cr_min <= cr <= target_cr_max:
                best_matrix_tfn = matrix_tfn
                best_matrix_defuzz = matrix_defuzz
                final_cr = cr
                repaired = (iteration > 0)
                break
            
            if cr < target_cr_min:
                noise_std += 0.05
            elif cr > target_cr_max:
                noise_std = max(0.01, noise_std - 0.05)
                
        if best_matrix_tfn is None:
            matrix_tfn = [[(1.0, 1.0, 1.0) for _ in range(n)] for _ in range(n)]
            matrix_defuzz = np.zeros((n, n))
            for i in range(n):
                matrix_defuzz[i, i] = 1.0
                for j in range(i + 1, n):
                    l, m, u = self._to_tfn(base_matrix[i, j])
                    matrix_tfn[i][j] = (l, m, u)
                    matrix_tfn[j][i] = (1.0/u, 1.0/m, 1.0/l)
                    matrix_defuzz[i, j] = (l + 2*m + u) / 4.0
                    matrix_defuzz[j, i] = (1.0/u + 2.0/m + 1.0/l) / 4.0
            _, _, _, cr = self._compute_ahp_metrics(matrix_defuzz)
            best_matrix_tfn = matrix_tfn
            best_matrix_defuzz = matrix_defuzz
            final_cr = cr
            repaired = True
            
        return {
            "matrix_tfn": best_matrix_tfn,
            "matrix_defuzz": best_matrix_defuzz,
            "original_cr": original_cr,
            "final_cr": final_cr,
            "repaired": repaired,
            "repair_iterations": iteration
        }

    def generate(self, scenarios: list[dict], n_experts_per_scenario: int = 3) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generates direct weights and AHP matrices/weights for given scenarios.
        
        scenarios: List of dicts e.g., [{"scenario_id": "SCN-2020-FMC", "year": 2020, "industry": "FMCG", "entity_type": "supplier"}]
        """
        direct_weights = []
        ahp_matrices = []
        ahp_weights = []
        
        expert_counter = 1
        
        for scenario in scenarios:
            entity_type = scenario["entity_type"]
            industry = scenario["industry"]
            year = scenario["year"]
            scen_id = scenario["scenario_id"]
            
            # Identify configurations
            criteria_list = config.SUPPLIER_CRITERIA if entity_type == "supplier" else config.BUYER_CRITERIA
            criteria_names = [c["name"] for c in criteria_list]
            industry_profile = config.INDUSTRY_PROFILES[industry]
            tendencies = industry_profile[f"{entity_type}_weight_tendencies"]
            
            # Identify evaluators
            org_type = "Buyer" if entity_type == "supplier" else "Supplier"
            roles_dict = config.SUPPLIER_EVAL_ROLES if entity_type == "supplier" else config.BUYER_EVAL_ROLES
            available_roles = list(roles_dict.keys())
            
            for _ in range(n_experts_per_scenario):
                expert_id = f"EXP-{expert_counter:05d}"
                expert_counter += 1
                
                # Sample role
                role = self.rng.choice(available_roles)
                role_biases = roles_dict[role]["weight_biases"]
                
                # Sample continuous ideal priorities (latent preferences)
                ideal_priorities = []
                raw_direct_scores = []
                
                for crit in criteria_names:
                    mean, std = tendencies[crit]
                    bias = role_biases.get(crit, 0.0)
                    
                    # True preference score
                    true_score = self.rng.normal(mean + bias, std)
                    true_score = np.clip(true_score, 1.0, 10.0)
                    
                    ideal_priorities.append(true_score)
                    
                    # Direct Weight mapping (round to integer 1-10)
                    direct_wt = int(round(true_score))
                    raw_direct_scores.append(direct_wt)
                    
                # Store direct weights
                sum_direct = sum(raw_direct_scores)
                for i, crit in enumerate(criteria_names):
                    d_val = raw_direct_scores[i]
                    direct_weights.append({
                        "expert_id": expert_id,
                        "industry": industry,
                        "organization_type": org_type,
                        "role": role,
                        "entity_type": entity_type,
                        "scenario_id": scen_id,
                        "year": year,
                        "criterion": crit,
                        "direct_weight": d_val,
                        "interpretation": config.get_weight_interpretation(d_val),
                        "normalized_weight": round(d_val / sum_direct, 4)
                    })
                    
                # ── Generate AHP Matrix ──
                # Choose target CR band
                bands = list(config.DEFAULT_CR_DISTRIBUTION.keys())
                probs = list(config.DEFAULT_CR_DISTRIBUTION.values())
                target_band = self.rng.choice(bands, p=probs)
                
                # Determine min and max CR permitted for this matrix
                min_cr, max_cr = config.CR_BANDS[target_band]
                
                # Generate matrix via controlled noise
                ideal_array = np.array(ideal_priorities)
                ahp_result = self._generate_pairwise_matrix(ideal_array, min_cr, max_cr)
                matrix_tfn = ahp_result["matrix_tfn"]
                matrix_defuzz = ahp_result["matrix_defuzz"]
                
                # Compute final analytics
                w, l_max, ci, cr = self._compute_ahp_metrics(matrix_defuzz)
                is_consistent = "consistent" if cr <= config.CR_THRESHOLD else "inconsistent"
                
                matrix_id = f"{scen_id}_{expert_id}"
                
                # Store pairwise matrix
                for i in range(len(criteria_names)):
                    for j in range(len(criteria_names)):
                        l, m, u = matrix_tfn[i][j]
                        ahp_matrices.append({
                            "matrix_id": matrix_id,
                            "expert_id": expert_id,
                            "industry": industry,
                            "role": role,
                            "entity_type": entity_type,
                            "scenario_id": scen_id,
                            "year": year,
                            "criterion_i": criteria_names[i],
                            "criterion_j": criteria_names[j],
                            "lower": float(l),
                            "middle": float(m),
                            "upper": float(u)
                        })
                        
                # Store AHP weights
                for i, crit in enumerate(criteria_names):
                    ahp_weights.append({
                        "expert_id": expert_id,
                        "industry": industry,
                        "role": role,
                        "entity_type": entity_type,
                        "scenario_id": scen_id,
                        "year": year,
                        "criterion": crit,
                        "ahp_weight": float(w[i]),
                        "lambda_max": round(l_max, 4),
                        "CI": round(ci, 4),
                        "RI": config.SAATY_RI.get(len(criteria_names), 1.45),
                        "CR": round(cr, 4),
                        "consistency_status": is_consistent,
                        "original_cr": round(ahp_result["original_cr"], 4),
                        "final_cr": round(ahp_result["final_cr"], 4),
                        "repaired": ahp_result["repaired"],
                        "repair_iterations": ahp_result["repair_iterations"],
                        "target_band": target_band
                    })

        df_direct = pd.DataFrame(direct_weights)
        df_matrices = pd.DataFrame(ahp_matrices)
        df_ahp_weights = pd.DataFrame(ahp_weights)
        
        return df_direct, df_matrices, df_ahp_weights
