"""
dataset_dialog.py — Dialog for generating synthetic test datasets.

Runs the generation process in a background thread to prevent UI freezing.
"""

from __future__ import annotations

# stdlib
from typing import Any

# PyQt6
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# third-party
import pandas as pd

# local core
from app.core.criteria import CriteriaConfig
# local gui
from app.config import DIMENSIONS
from app.gui.widgets import make_scroll_area, make_status_label
from app.gui.workers import DatasetGenerationWorker


class DatasetGenerationDialog(QDialog):
    """Dialog to configure and execute synthetic dataset generation.

    Offloads the file-writing process to DatasetGenerationWorker.
    """

    def __init__(self, entity_type: str, parent: QWidget | None = None) -> None:
        """Initialize the dataset generation dialog.

        Args:
            entity_type: "supplier" or "buyer".
            parent: Parent widget.
        """
        super().__init__(parent)
        self.entity_type = entity_type.lower()
        self.criteria_names = CriteriaConfig.get_criteria_names(self.entity_type)
        self.worker: DatasetGenerationWorker | None = None

        self.setWindowTitle(f"Generate {entity_type.title()} Test Data")
        self.setFixedSize(DIMENSIONS["dialog_width"], DIMENSIONS["dialog_height"])

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the layout and widgets of the dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header banner
        header = QLabel(f"Synthetic {self.entity_type.title()} Data Generator")
        header.setProperty("role", "header")
        layout.addWidget(header)

        # Settings Pane
        settings_container = QWidget()
        settings_container.setContentsMargins(14, 0, 14, 0)
        form_layout = QFormLayout(settings_container)
        form_layout.setSpacing(10)

        # 1. Number of Entities
        self.n_spin = QSpinBox()
        self.n_spin.setRange(10, 10000)
        self.n_spin.setSingleStep(10)
        self.n_spin.setValue(100)
        form_layout.addRow("Number of entities (10-10000):", self.n_spin)

        # 2. Random Seed Row
        seed_widget = QWidget()
        seed_layout = QHBoxLayout(seed_widget)
        seed_layout.setContentsMargins(0, 0, 0, 0)
        seed_layout.setSpacing(10)

        self.seed_check = QCheckBox("Enable seed")
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(42)
        self.seed_spin.setEnabled(False)
        self.seed_check.toggled.connect(self.seed_spin.setEnabled)

        seed_layout.addWidget(self.seed_check)
        seed_layout.addWidget(self.seed_spin)
        seed_layout.addStretch()

        form_layout.addRow("Reproducibility:", seed_widget)
        layout.addWidget(settings_container)

        # Generate Button & Status
        actions_container = QWidget()
        actions_container.setContentsMargins(14, 0, 14, 0)
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setSpacing(8)

        self.status_lbl = make_status_label("Configure settings above and click generate.", "neutral")
        self.generate_btn = QPushButton("Generate Dataset")
        self.generate_btn.setProperty("class", "success")
        self.generate_btn.style().unpolish(self.generate_btn)
        self.generate_btn.style().polish(self.generate_btn)
        self.generate_btn.clicked.connect(self.start_generation)

        actions_layout.addWidget(self.status_lbl)
        actions_layout.addWidget(self.generate_btn)
        layout.addWidget(actions_container)

        # Preview Section (Top 5 rows)
        preview_container = QWidget()
        preview_container.setContentsMargins(14, 0, 14, 0)
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setSpacing(6)
        
        preview_lbl = QLabel("Dataset Preview (First 5 records):")
        preview_lbl.setProperty("role", "subheader")
        preview_lbl.style().unpolish(preview_lbl)
        preview_lbl.style().polish(preview_lbl)
        preview_layout.addWidget(preview_lbl)

        self.preview_table = QTableWidget()
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        preview_layout.addWidget(self.preview_table)
        layout.addWidget(preview_container)

        # Bottom Close button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(14, 0, 14, 14)
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    # ── Logics ──────────────────────────────────────────────────────────────

    def start_generation(self) -> None:
        """Lock inputs and launch the dataset generator thread."""
        n_entities = self.n_spin.value()
        seed = self.seed_spin.value() if self.seed_check.isChecked() else None

        self.n_spin.setEnabled(False)
        self.seed_check.setEnabled(False)
        self.seed_spin.setEnabled(False)
        self.generate_btn.setEnabled(False)

        self.status_lbl.setText("Generating synthetic dataset in background...")
        self.status_lbl.setProperty("status", "neutral")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        # Start worker QThread
        self.worker = DatasetGenerationWorker(self.entity_type, n_entities, seed, self)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def on_generation_finished(self, df: pd.DataFrame) -> None:
        """Unlock inputs, display preview, and signal success.

        Args:
            df: Generated DataFrame returned from the worker thread.
        """
        self.n_spin.setEnabled(True)
        self.seed_check.setEnabled(True)
        self.seed_spin.setEnabled(self.seed_check.isChecked())
        self.generate_btn.setEnabled(True)

        self.status_lbl.setText(f"Successfully generated {len(df)} records!")
        self.status_lbl.setProperty("status", "success")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        # Populate top 5 rows preview
        self.populate_preview(df.head(5))

    def on_generation_error(self, error_msg: str) -> None:
        """Unlock inputs and display the error message.

        Args:
            error_msg: Error message details.
        """
        self.n_spin.setEnabled(True)
        self.seed_check.setEnabled(True)
        self.seed_spin.setEnabled(self.seed_check.isChecked())
        self.generate_btn.setEnabled(True)

        self.status_lbl.setText("Dataset generation failed.")
        self.status_lbl.setProperty("status", "error")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        QMessageBox.critical(self, "Error", f"Could not generate dataset:\n{error_msg}")

    def populate_preview(self, df: pd.DataFrame) -> None:
        """Populate the preview table with the top 5 records.

        Args:
            df: DataFrame containing the first 5 records of the dataset.
        """
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        
        # Wrap criteria headers to avoid clipping at large font sizes
        import textwrap
        wrapped_headers = []
        for col in df.columns:
            if col == "ID":
                wrapped_headers.append("Company Name")  # "ID" is actually the Company Name
            else:
                wrapped_headers.append("\n".join(textwrap.wrap(col, 15)))
        self.preview_table.setHorizontalHeaderLabels(wrapped_headers)

        for row_idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem()
                if isinstance(value, (int, float)):
                    item.setData(Qt.ItemDataRole.DisplayRole, value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setText(str(value))
                self.preview_table.setItem(row_idx, col_idx, item)

        # Style headers & make columns non-resizable by user
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Force layout recalculation and adjust dialog size to fit table exactly
        self.preview_table.resizeColumnsToContents()
        table_width = 0
        for col in range(self.preview_table.columnCount()):
            table_width += self.preview_table.columnWidth(col)
            
        # Update dialog to exactly the width needed for all columns
        dialog_width = max(DIMENSIONS["dialog_width"], table_width + 80)
        self.setFixedSize(dialog_width, DIMENSIONS["dialog_height"])
