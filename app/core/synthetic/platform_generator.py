"""
Platform Dataset Generator.

Orchestrates full synthetic generation of the evolved 19-sheet MCDM platform architecture
as defined in syn_data_slim.xlsx.
"""

from __future__ import annotations

import time
from pathlib import Path
import numpy as np
import pandas as pd

from .company_factory import CompanyFactory
from .rating_engine import RatingEngine
from .ahp_generator import AHPGenerator
from .matching_engine import MatchingEngine
from .business_vars_engine import BusinessVarsEngine
from . import config


class PlatformDatasetGenerator:
    """End-to-end generator for the slim, modular 19-sheet dataset."""

    def __init__(self, seed: int = config.DEFAULT_SEED) -> None:
        self.seed = seed
        self.cf = CompanyFactory(seed=seed)
        self.re = RatingEngine(seed=seed)
        self.ahp = AHPGenerator(seed=seed)
        self.me = MatchingEngine(seed=seed)
        self.bve = BusinessVarsEngine(seed=seed)

    def generate_all(
        self,
        n_suppliers: int = 100,
        n_buyers: int = 25,
        start_year: int = config.DEFAULT_YEAR_START,
        end_year: int = config.DEFAULT_YEAR_END,
    ) -> dict[str, pd.DataFrame]:
        """
        Executes generation for all 19 sheets and returns them as a dictionary of DataFrames.
        """
        eval_years = list(range(start_year, end_year + 1))

        # 1. Entities (Internal full profiles for simulation)
        suppliers_full = self.cf.generate("supplier", n_suppliers, start_year=start_year)
        buyers_full = self.cf.generate("buyer", n_buyers, start_year=start_year)

        # Public slim profiles
        suppliers_slim = self.cf.to_slim(suppliers_full)
        buyers_slim = self.cf.to_slim(buyers_full)

        # 2. Ratings & Events
        sup_ratings_raw, sup_events = self.re.generate(
            suppliers_full, "supplier", start_year=start_year, end_year=end_year
        )
        buy_ratings_raw, buy_events = self.re.generate(
            buyers_full, "buyer", start_year=start_year, end_year=end_year
        )

        sup_yearly = self.re.aggregate_yearly(sup_ratings_raw)
        buy_yearly = self.re.aggregate_yearly(buy_ratings_raw)

        # Public slim ratings
        supplier_ratings_slim = self.re.to_slim_ratings(sup_yearly)
        buyer_ratings_slim = self.re.to_slim_ratings(buy_yearly)

        # De-normalized Qualification (1 row per entity-year)
        sup_qual = self.re.extract_qualification(sup_yearly)
        buy_qual = self.re.extract_qualification(buy_yearly)
        qualification_df = pd.concat([sup_qual, buy_qual], ignore_index=True).sort_values(
            ["entity_id", "year"]
        ).reset_index(drop=True)

        # Combined slim Events Log
        all_events_raw = pd.concat([sup_events, buy_events], ignore_index=True)
        events_log_slim = self.re.to_slim_events(all_events_raw)

        # 3. Expert Evaluations & Fuzzy AHP Layer
        ahp_pack = self.ahp.generate_slim(years=eval_years)
        experts_df = ahp_pack["Experts"]
        direct_weights_df = ahp_pack["Direct_Weights"]
        ahp_pairwise_df = ahp_pack["AHP_Pairwise"]
        ahp_pairwise_fuzzy_df = ahp_pack["AHP_Pairwise_Fuzzy"]
        fuzzy_rules_df = ahp_pack["Fuzzy_Rules"]
        ahp_weights_df = ahp_pack["AHP_Weights"]
        ahp_consistency_df = ahp_pack["AHP_Consistency"]

        # 4. Relationships (Bipartite capacity-constrained matching)
        relationships_df = self.me.generate_relationships(
            buyers_full, suppliers_full, start_year=start_year, end_year=end_year
        )

        # 5. Business Variables (Operational metrics)
        sup_bus_vars_slim = self.bve.generate_supplier_vars(
            suppliers_full, sup_yearly, slim=True
        )
        buy_bus_vars_slim = self.bve.generate_buyer_vars(
            buyers_full, buy_yearly, slim=True
        )

        # 6. Metadata & Reference sheets
        notes_df = pd.DataFrame({"note": config.PLATFORM_NOTES})
        removed_cols_df = pd.DataFrame(config.REMOVED_COLUMNS_AUDIT)
        criteria_df = pd.DataFrame(config.CRITERIA_METADATA)

        # Package in exact canonical 19-sheet order
        return {
            "Notes": notes_df,
            "Removed_Columns": removed_cols_df,
            "Criteria": criteria_df,
            "Suppliers": suppliers_slim,
            "Buyers": buyers_slim,
            "Supplier_Ratings": supplier_ratings_slim,
            "Buyer_Ratings": buyer_ratings_slim,
            "Qualification": qualification_df,
            "Events_Log": events_log_slim,
            "Experts": experts_df,
            "Direct_Weights": direct_weights_df,
            "AHP_Pairwise": ahp_pairwise_df,
            "AHP_Pairwise_Fuzzy": ahp_pairwise_fuzzy_df,
            "Fuzzy_Rules": fuzzy_rules_df,
            "AHP_Weights": ahp_weights_df,
            "AHP_Consistency": ahp_consistency_df,
            "Supplier_Business_Vars": sup_bus_vars_slim,
            "Buyer_Business_Vars": buy_bus_vars_slim,
            "Relationships": relationships_df,
        }

    def export_to_excel(
        self,
        sheets_dict: dict[str, pd.DataFrame],
        output_path: str | Path,
    ) -> None:
        """Export all generated sheets into a single multi-tab Excel workbook."""
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    def export_to_csv_dir(
        self,
        sheets_dict: dict[str, pd.DataFrame],
        output_dir: str | Path,
    ) -> None:
        """Export all generated tables into individual CSV files."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, df in sheets_dict.items():
            df.to_csv(out_dir / f"{name}.csv", index=False)
