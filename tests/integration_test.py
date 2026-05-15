"""Integration test for the MCDM DSS system."""

from __future__ import annotations

import sys
from pathlib import Path

# Support both relative imports (module) and absolute imports (script run)
app_dir = Path(__file__).resolve().parent.parent / "app"
if str(app_dir.parent) not in sys.path:
    sys.path.insert(0, str(app_dir.parent))

try:
    from app.config import BASE_DIR
    from app.core.company_manager import CompanyManager
    from app.core.criteria import CriteriaConfig
    from app.core.dataset_generator import DatasetGenerator
    from app.core.solver_engine import MCDMSolverEngine
    from app.core.weight_manager import WeightSchemeManager
    from app.export.chart_generator import ChartGenerator
    from app.export.excel_exporter import ExcelExporter
except ImportError:
    # Fallback: add and retry
    sys.path.insert(0, str(app_dir.parent))
    from app.config import BASE_DIR
    from app.core.company_manager import CompanyManager
    from app.core.criteria import CriteriaConfig
    from app.core.dataset_generator import DatasetGenerator
    from app.core.solver_engine import MCDMSolverEngine
    from app.core.weight_manager import WeightSchemeManager
    from app.export.chart_generator import ChartGenerator
    from app.export.excel_exporter import ExcelExporter


def test_full_workflow() -> None:
    """Run a complete end-to-end test of the system."""
    print("=" * 60)
    print("MCDM DSS — INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize managers
    company_manager = CompanyManager()
    weight_manager = WeightSchemeManager()
    dataset_generator = DatasetGenerator()
    solver_engine = MCDMSolverEngine()
    excel_exporter = ExcelExporter()
    chart_generator = ChartGenerator()
    
    # ─────────────────────────────────────────────────
    # Step 1: Generate 50 synthetic suppliers
    # ─────────────────────────────────────────────────
    print("\n[1] Generating 50 synthetic suppliers...")
    dataset = dataset_generator.generate("supplier", 50, seed=42)
    print(f"✓ Generated {len(dataset)} suppliers")
    print(f"  Dataset columns: {list(dataset.columns)}")
    print(f"  First 3 rows:\n{dataset.head(3).to_string()}\n")
    
    # ─────────────────────────────────────────────────
    # Step 2: Create one weight scheme
    # ─────────────────────────────────────────────────
    print("[2] Creating one weight scheme...")
    criteria_names = CriteriaConfig.get_criteria_names("supplier")
    weights = {name: 1.0 for name in criteria_names}  # Equal weights
    
    weight_manager.save_scheme("supplier", "Equal Weights", weights)
    print("✓ Saved weight scheme: 'Equal Weights'")
    
    loaded_weights = weight_manager.load_scheme("supplier", "Equal Weights")
    print(f"  Normalized weights (sample):")
    for i, (name, w) in enumerate(list(loaded_weights.items())[:3]):
        print(f"    {name}: {w:.4f}")
    print(f"    ... (9 criteria total)\n")
    
    # ─────────────────────────────────────────────────
    # Step 3: Run all 3 MCDM methods
    # ─────────────────────────────────────────────────
    print("[3] Running all 3 MCDM methods...")
    analysis_results = solver_engine.run_analysis(
        "supplier",
        dataset,
        ["Equal Weights"],
        ["AHP", "TOPSIS", "VIKOR"],
        v=0.5,
    )
    print("✓ Analysis complete")
    print(f"  Result DataFrame shape: {analysis_results.shape}")
    print(f"  Result columns: {list(analysis_results.columns)}\n")
    
    # Show sample top 3 results
    print("  Sample top 3 AHP results:")
    ahp_cols = [col for col in analysis_results.columns if "AHP" in col and "Score" in col]
    if ahp_cols:
        top_3_ahp = analysis_results.nsmallest(3, "AHP_equal_weights_Rank")
        for _, row in top_3_ahp.iterrows():
            score_col = ahp_cols[0]
            print(f"    {row['ID']}: {row[score_col]:.4f}")
    print()
    
    # ─────────────────────────────────────────────────
    # Step 4: Generate Excel report
    # ─────────────────────────────────────────────────
    print("[4] Generating Excel report...")
    
    # Prepare results in expected format
    export_results = {}
    for method in ["AHP", "TOPSIS", "VIKOR"]:
        method_cols = [col for col in analysis_results.columns if method in col]
        if method_cols:
            score_col = [c for c in method_cols if "Score" in c][0]
            rank_col = [c for c in method_cols if "Rank" in c][0]
            export_results[f"{method}_equal_weights"] = analysis_results[["ID", score_col, rank_col]].copy()
            export_results[f"{method}_equal_weights"].columns = ["ID", "Score", "Rank"]
    
    excel_path = excel_exporter.export("supplier", export_results)
    print(f"✓ Excel file created: {excel_path.name}")
    print(f"  File size: {excel_path.stat().st_size / 1024:.1f} KB\n")
    
    # ─────────────────────────────────────────────────
    # Step 5: Generate charts
    # ─────────────────────────────────────────────────
    print("[5] Generating charts...")
    chart_paths = chart_generator.generate_all_charts(export_results, "supplier")
    print(f"✓ Generated {len(chart_paths)} charts")
    for chart_path in chart_paths:
        print(f"  - {chart_path.name}")
    print()
    
    # ─────────────────────────────────────────────────
    # Final Summary
    # ─────────────────────────────────────────────────
    print("=" * 60)
    print("✅ INTEGRATION TEST PASSED")
    print("=" * 60)
    print("\nSummary:")
    print(f"  • Generated 50 suppliers with 9 criteria each")
    print(f"  • Created 1 weight scheme (equal weights)")
    print(f"  • Ran 3 MCDM methods (AHP, TOPSIS, VIKOR)")
    print(f"  • Generated 1 Excel workbook with results")
    print(f"  • Generated {len(chart_paths)} visualization charts")
    print(f"\nOutput directory: {BASE_DIR / 'data' / 'results'}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_full_workflow()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
