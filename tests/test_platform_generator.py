"""Tests for the 19-sheet synthetic platform dataset generator and Fuzzy AHP engine."""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.core.synthetic import PlatformDatasetGenerator
from app.core.synthetic import config
from app.core.ahp import AHPSolver


@pytest.fixture(scope="module")
def generated_platform_data():
    """Generates a small test dataset across 3 years."""
    gen = PlatformDatasetGenerator(seed=42)
    return gen.generate_all(n_suppliers=30, n_buyers=10, start_year=2021, end_year=2023)


def test_platform_19_sheets_present(generated_platform_data):
    """Ensure all 19 sheets are present in canonical order."""
    expected_order = [
        "Notes",
        "Removed_Columns",
        "Criteria",
        "Suppliers",
        "Buyers",
        "Supplier_Ratings",
        "Buyer_Ratings",
        "Qualification",
        "Events_Log",
        "Experts",
        "Direct_Weights",
        "AHP_Pairwise",
        "AHP_Pairwise_Fuzzy",
        "Fuzzy_Rules",
        "AHP_Weights",
        "AHP_Consistency",
        "Supplier_Business_Vars",
        "Buyer_Business_Vars",
        "Relationships",
    ]
    actual_sheets = list(generated_platform_data.keys())
    assert actual_sheets == expected_order, f"Sheet ordering mismatch: {actual_sheets}"


def test_suppliers_buyers_slim_schema(generated_platform_data):
    """Ensure latent factors and removed columns are stripped from public sheets."""
    sup_df = generated_platform_data["Suppliers"]
    buy_df = generated_platform_data["Buyers"]
    
    expected_cols = [
        "entity_id", "industry", "country", "company_size", "strategic_segment",
        "risk_segment", "creation_year", "active_status", "deactivation_year"
    ]
    assert list(sup_df.columns) == expected_cols
    assert "operational_capability" not in sup_df.columns
    assert "financial_health" not in sup_df.columns
    assert "company_name" not in sup_df.columns
    assert len(sup_df) == 30

    assert list(buy_df.columns) == expected_cols
    assert "operational_capability" not in buy_df.columns
    assert len(buy_df) == 10


def test_ahp_pairwise_upper_triangle(generated_platform_data):
    """Ensure pairwise comparisons store only upper triangle (36 pairs per 9x9 matrix)."""
    pairwise_df = generated_platform_data["AHP_Pairwise"]
    fuzzy_df = generated_platform_data["AHP_Pairwise_Fuzzy"]
    
    # 70 experts * 3 years = 210 matrices
    # 210 matrices * 36 pairs = 7560 rows
    assert len(pairwise_df) == 70 * 3 * 36
    assert len(fuzzy_df) == 70 * 3 * 36
    
    # Verify no diagonal pairs (criterion_i == criterion_j)
    assert not (pairwise_df["criterion_i"] == pairwise_df["criterion_j"]).any()


def test_fuzzy_tfn_properties(generated_platform_data):
    """Ensure all Triangular Fuzzy Numbers satisfy l <= m <= u and non-negativity."""
    fuzzy_df = generated_platform_data["AHP_Pairwise_Fuzzy"]
    
    assert (fuzzy_df["l"] <= fuzzy_df["m"]).all(), "Found l > m in TFNs"
    assert (fuzzy_df["m"] <= fuzzy_df["u"]).all(), "Found m > u in TFNs"
    assert (fuzzy_df["l"] > 0).all(), "Found non-positive lower bound in TFNs"
    assert set(fuzzy_df["confidence"].unique()).issubset({"High", "Medium", "Low"})


def test_ahp_consistency_bounds(generated_platform_data):
    """Ensure all generated AHP matrices satisfy the consistency threshold CR <= 0.10."""
    consistency_df = generated_platform_data["AHP_Consistency"]
    assert len(consistency_df) == 70 * 3
    assert (consistency_df["CR"] <= 0.10).all(), f"Found CR > 0.10: {consistency_df[consistency_df['CR'] > 0.10]}"
    assert (consistency_df["CR"] >= 0.0).all()


def test_ahp_solver_with_upper_triangle(generated_platform_data):
    """Ensure AHPSolver successfully solves upper-triangle fuzzy matrices via Buckley's method."""
    fuzzy_df = generated_platform_data["AHP_Pairwise_Fuzzy"]
    sub_df = fuzzy_df[(fuzzy_df["expert_id"] == "EXP-00001") & (fuzzy_df["year"] == 2021)]
    assert len(sub_df) == 36
    
    solver = AHPSolver()
    derived = solver.derive_weights(sub_df)
    
    assert len(derived) == 9
    assert abs(sum(derived.values()) - 1.0) < 1e-4
    for w in derived.values():
        assert 0.0 < w < 1.0


def test_qualification_sheet_denormalized(generated_platform_data):
    """Ensure qualification sheet contains 1 row per entity-year with boolean is_qualified."""
    qual_df = generated_platform_data["Qualification"]
    assert list(qual_df.columns) == ["entity_id", "year", "is_qualified"]
    assert qual_df["is_qualified"].isin([True, False]).all()
    # No duplicate (entity_id, year)
    assert not qual_df.duplicated(subset=["entity_id", "year"]).any()
