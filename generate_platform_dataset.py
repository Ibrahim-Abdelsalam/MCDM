#!/usr/bin/env python3
"""
CLI script to generate the 19-sheet synthetic MCDM platform dataset.

Reproduces the modular architecture of syn_data_slim.xlsx with:
- 19 sheets in canonical order
- Upper-triangle pairwise matrices
- Triangular Fuzzy Numbers (TFNs) with confidence mapping
- Longitudinal expert panel (70 experts)
- De-normalized qualifications
- Slim business variables and relationships
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure app package is importable
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.core.synthetic import PlatformDatasetGenerator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 19-sheet MCDM platform synthetic dataset."
    )
    parser.add_argument(
        "--suppliers",
        type=int,
        default=100,
        help="Number of suppliers to simulate (default: 100)",
    )
    parser.add_argument(
        "--buyers",
        type=int,
        default=25,
        help="Number of buyers to simulate (default: 25)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2018,
        help="Starting evaluation year (default: 2018)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2023,
        help="Ending evaluation year (default: 2023)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output-excel",
        type=str,
        default="datasets/syn_data_platform.xlsx",
        help="Path to save multi-sheet Excel workbook (default: datasets/syn_data_platform.xlsx)",
    )
    parser.add_argument(
        "--output-csv-dir",
        type=str,
        default=None,
        help="Optional directory to save individual CSV files for each sheet",
    )

    args = parser.parse_args()

    print("=" * 65)
    print("MCDM PLATFORM DATASET GENERATOR")
    print("=" * 65)
    print(f"  • Suppliers:      {args.suppliers}")
    print(f"  • Buyers:         {args.buyers}")
    print(f"  • Evaluation span: {args.start_year} - {args.end_year}")
    print(f"  • Seed:           {args.seed}")
    print(f"  • Target Excel:   {args.output_excel}")
    if args.output_csv_dir:
        print(f"  • Target CSV Dir: {args.output_csv_dir}")
    print("=" * 65)

    start_time = time.time()
    generator = PlatformDatasetGenerator(seed=args.seed)

    print("\nGenerating 19 platform sheets...")
    sheets = generator.generate_all(
        n_suppliers=args.suppliers,
        n_buyers=args.buyers,
        start_year=args.start_year,
        end_year=args.end_year,
    )

    print("\nGenerated Sheet Inventory:")
    print(f"  {'#':<3} | {'Sheet Name':<25} | {'Rows':<8} | {'Cols':<6}")
    print("  " + "-" * 50)
    for idx, (name, df) in enumerate(sheets.items(), 1):
        print(f"  {idx:<3} | {name:<25} | {len(df):<8} | {len(df.columns):<6}")

    # Consistency verification
    consistency_df = sheets["AHP_Consistency"]
    max_cr = consistency_df["CR"].max()
    all_consistent = (consistency_df["CR"] <= 0.10).all()
    print(f"\nAHP Consistency Check:")
    print(f"  • Total matrices: {len(consistency_df)}")
    print(f"  • Max CR:         {max_cr:.4f}")
    print(f"  • Status:         {'✅ ALL PASS (CR <= 0.10)' if all_consistent else '❌ INCONSISTENT'}")

    # Export to Excel
    out_excel = repo_root / args.output_excel
    print(f"\nExporting workbook to {out_excel}...")
    generator.export_to_excel(sheets, out_excel)
    print(f"✓ Excel saved ({out_excel.stat().st_size / 1024:.1f} KB)")

    # Export to CSV if requested
    if args.output_csv_dir:
        out_csv = repo_root / args.output_csv_dir
        print(f"Exporting CSVs to {out_csv}...")
        generator.export_to_csv_dir(sheets, out_csv)
        print("✓ All 19 CSVs exported.")

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.2f} seconds.")
    print("=" * 65)


if __name__ == "__main__":
    main()
