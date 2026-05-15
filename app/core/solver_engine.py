"""MCDM solver orchestrator that manages analysis workflow."""

from __future__ import annotations

import pandas as pd

from .ahp import AHPSolver
from .topsis import TOPSISSolver
from .vikor import VIKORSolver
from .weight_manager import WeightSchemeManager


class MCDMSolverEngine:
    """Orchestrate MCDM analysis: data loading, normalization, and method execution."""

    def __init__(self) -> None:
        """Initialize the solver engine."""
        self.weight_manager = WeightSchemeManager()
        self.ahp_solver = AHPSolver()
        self.topsis_solver = TOPSISSolver()
        self.vikor_solver = VIKORSolver()

    def run_analysis(
        self,
        entity_type: str,
        scores_df: pd.DataFrame,
        weight_scheme_names: list[str],
        methods: list[str],
        v: float = 0.5,
    ) -> pd.DataFrame:
        """
        Run complete MCDM analysis across one or more weight schemes and methods.
        
        Args:
            entity_type: "supplier" or "buyer"
            scores_df: DataFrame with ID column and criterion score columns
            weight_scheme_names: list of weight scheme names to apply
            methods: list of method names: "AHP", "TOPSIS", "VIKOR"
            v: VIKOR v parameter (0.0–1.0, default 0.5)
        
        Returns:
            Merged DataFrame with columns: [ID, {METHOD}_{SCHEME}_Score, {METHOD}_{SCHEME}_Rank, ...]
        """
        if not weight_scheme_names:
            raise ValueError("At least one weight scheme must be selected.")
        if not methods:
            raise ValueError("At least one method must be selected.")
        
        valid_methods = {"AHP", "TOPSIS", "VIKOR"}
        invalid_methods = set(methods) - valid_methods
        if invalid_methods:
            raise ValueError(f"Unknown methods: {invalid_methods}")
        
        merged_results = scores_df[["ID"]].copy()
        
        for scheme_name in weight_scheme_names:
            # Load and normalize weight scheme
            weight_vector = self.weight_manager.load_scheme(entity_type, scheme_name)
            
            # Sanitize scheme name for column naming
            safe_scheme_name = scheme_name.replace(" ", "_").replace("-", "_")[:20].lower()
            
            # Run requested methods
            if "AHP" in methods:
                ahp_result = self.ahp_solver.solve(weight_vector, scores_df)
                merged_results[f"AHP_{safe_scheme_name}_Score"] = ahp_result["AHP_Score"]
                merged_results[f"AHP_{safe_scheme_name}_Rank"] = ahp_result["AHP_Rank"]
            
            if "TOPSIS" in methods:
                topsis_result = self.topsis_solver.solve(weight_vector, scores_df)
                merged_results[f"TOPSIS_{safe_scheme_name}_Score"] = topsis_result["TOPSIS_Score"]
                merged_results[f"TOPSIS_{safe_scheme_name}_Rank"] = topsis_result["TOPSIS_Rank"]
            
            if "VIKOR" in methods:
                vikor_result = self.vikor_solver.solve(weight_vector, scores_df, v=v)
                merged_results[f"VIKOR_{safe_scheme_name}_Score"] = vikor_result["VIKOR_Score"]
                merged_results[f"VIKOR_{safe_scheme_name}_Rank"] = vikor_result["VIKOR_Rank"]
        
        return merged_results
