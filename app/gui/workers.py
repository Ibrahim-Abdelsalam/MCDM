"""
workers.py — QThread workers for running heavy computations in the background.

This keeps the GUI responsive when generating datasets or running multi-scheme
analyses with charts and Excel exports.
"""

from __future__ import annotations

# stdlib
from pathlib import Path
from typing import Any

# PyQt6
from PyQt6.QtCore import QThread, pyqtSignal

# third-party
import pandas as pd

# local core
from app.core.dataset_generator import DatasetGenerator
from app.core.solver_engine import MCDMSolverEngine
# local export
from app.export.chart_generator import ChartGenerator
from app.export.excel_exporter import ExcelExporter


class DatasetGenerationWorker(QThread):
    """Worker QThread for generating synthetic MCDM datasets.

    Emits ``finished(pd.DataFrame)`` upon success, or ``error(str)`` on failure.
    """

    # Signals defined at class level
    finished: pyqtSignal = pyqtSignal(pd.DataFrame)
    error: pyqtSignal = pyqtSignal(str)

    def __init__(
        self,
        entity_type: str,
        n_entities: int,
        seed: int | None = None,
        parent: Any = None,
    ) -> None:
        """Initialize the dataset worker.

        Args:
            entity_type: "supplier" or "buyer".
            n_entities: Number of entities to generate.
            seed: Optional random seed.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.entity_type = entity_type
        self.n_entities = n_entities
        self.seed = seed

    def run(self) -> None:
        """Run the dataset generation."""
        try:
            generator = DatasetGenerator()
            df = generator.generate(self.entity_type, self.n_entities, seed=self.seed)
            self.finished.emit(df)
        except Exception as e:
            self.error.emit(str(e))


class AnalysisWorker(QThread):
    """Worker QThread for orchestrating solver execution, charting, and Excel exports.

    Emits ``finished(dict, list, Path)`` on success with:
      - Dictionary mapping "{METHOD}_{SCHEME}" to cleaned results DataFrames
      - List of generated chart Path objects
      - Path to the generated Excel workbook
    Emits ``error(str)`` on failure.
    """

    # Signals defined at class level
    finished: pyqtSignal = pyqtSignal(dict, list, Path)
    error: pyqtSignal = pyqtSignal(str)

    def __init__(
        self,
        entity_type: str,
        scores_df: pd.DataFrame,
        selected_schemes: list[str],
        methods: list[str],
        v_param: float,
        parent: Any = None,
    ) -> None:
        """Initialize the analysis worker.

        Args:
            entity_type: "supplier" or "buyer".
            scores_df: DataFrame containing the loaded scores.
            selected_schemes: List of weight scheme names to apply.
            methods: List of method names ("AHP", "TOPSIS", "VIKOR").
            v_param: VIKOR v parameter.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.entity_type = entity_type
        self.scores_df = scores_df
        self.selected_schemes = selected_schemes
        self.methods = methods
        self.v_param = v_param

    def run(self) -> None:
        """Run analysis, chart generation, and excel export."""
        try:
            solver_engine = MCDMSolverEngine()
            chart_generator = ChartGenerator()
            excel_exporter = ExcelExporter()

            analysis_results = {}
            for scheme_name in self.selected_schemes:
                for method in self.methods:
                    result = solver_engine.run_analysis(
                        self.entity_type,
                        self.scores_df,
                        [scheme_name],
                        [method],
                        v=self.v_param,
                    )
                    # Unique key format consistent with old UI
                    key = f"{method}_{scheme_name.replace(' ', '_').replace('-', '_')[:20].lower()}"
                    analysis_results[key] = result

            # Reorganize results for display and export
            display_results: dict[str, pd.DataFrame] = {}
            for key, result_df in analysis_results.items():
                rank_cols = [col for col in result_df.columns if "Rank" in col]
                score_cols = [col for col in result_df.columns if "Score" in col]
                if rank_cols and score_cols:
                    rank_col = rank_cols[0]
                    score_col = score_cols[0]
                    export_df = result_df[["ID", score_col, rank_col]].copy()
                    export_df.columns = ["ID", "Score", "Rank"]
                    display_results[key] = export_df

            # Generate charts and excel
            chart_paths = chart_generator.generate_all_charts(display_results, self.entity_type)
            excel_path = excel_exporter.export(self.entity_type, display_results)

            self.finished.emit(display_results, chart_paths, excel_path)
        except Exception as e:
            self.error.emit(str(e))
