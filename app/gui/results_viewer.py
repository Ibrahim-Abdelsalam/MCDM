"""
results_viewer.py — Modeless dialog to display summary tables, visual charts, and Excel export links.

Uses QDesktopServices to open local documents directly on the OS desktop.
"""

from __future__ import annotations

# stdlib
from pathlib import Path
from typing import Any

# PyQt6
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# third-party
import pandas as pd

# local gui
from app.config import COLORS, DIMENSIONS
from app.gui.widgets import make_scroll_area


class ResultsViewWidget(QWidget):
    """Results viewer widget embedded in the analyzer dialog.

    Displays ranking tables, renders PNG charts, and provides direct click-to-open
    launch buttons for the generated Excel file.
    """

    def __init__(
        self,
        entity_type: str,
        display_results: dict[str, pd.DataFrame],
        chart_paths: list[Path],
        excel_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the results viewer.

        Args:
            entity_type: "supplier" or "buyer".
            display_results: Dict mapping scheme_method key to cleaned DataFrame.
            chart_paths: List of generated chart paths.
            excel_path: Path of the exported Excel spreadsheet.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.entity_type = entity_type.lower()
        self.display_results = display_results
        self.chart_paths = chart_paths
        self.excel_path = excel_path

        # No window title/size needed since it's an embedded widget

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog layout and widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header banner
        header = QLabel(f"{self.entity_type.title()} Analysis Results Output")
        header.setProperty("role", "header")
        layout.addWidget(header)

        # Top Navigation Buttons
        top_btn_layout = QHBoxLayout()
        top_btn_layout.setSpacing(10)
        self.summary_btn = QPushButton("View Summary Table")
        self.charts_btn = QPushButton("View Charts")
        self.export_btn = QPushButton("Export Results")
        
        self.summary_btn.setCheckable(True)
        self.charts_btn.setCheckable(True)
        self.export_btn.setCheckable(True)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.summary_btn, 0)
        self.btn_group.addButton(self.charts_btn, 1)
        self.btn_group.addButton(self.export_btn, 2)
        self.summary_btn.setChecked(True)
        
        top_btn_layout.addWidget(self.summary_btn)
        top_btn_layout.addWidget(self.charts_btn)
        top_btn_layout.addWidget(self.export_btn)
        layout.addLayout(top_btn_layout)

        # Stacked Widget for Views
        self.results_stack = QStackedWidget()
        layout.addWidget(self.results_stack)

        self._setup_table_tab()
        self._setup_charts_tab()
        self._setup_export_tab()
        
        self.btn_group.idClicked.connect(self.results_stack.setCurrentIndex)

        # Bottom Back button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(14, 0, 14, 14)
        btn_layout.addStretch()
        self.back_btn = QPushButton("← Back to Analyzer")
        btn_layout.addWidget(self.back_btn)
        layout.addLayout(btn_layout)

    def _setup_table_tab(self) -> None:
        """Set up the summary table tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(10)

        title = QLabel("Top 5 Rankings Across Combinations")
        title.setProperty("role", "subheader")
        tab_layout.addWidget(title)
        
        # Filter Group Box
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        # We need to collect unique values for our filters
        unique_methods = set()
        unique_schemes = set()
        unique_companies = set()
        unique_ranks = set()
        
        for key, df in self.display_results.items():
            parts = key.split("_")
            method = parts[0]
            scheme = "_".join(parts[1:])
            unique_methods.add(method)
            unique_schemes.add(scheme)
            
            top_5 = df.nsmallest(5, "Rank")
            for _, row in top_5.iterrows():
                unique_companies.add(str(row["ID"]))
                unique_ranks.add(str(int(row["Rank"])))

        # 1. Method Filter
        self.method_combo = QComboBox()
        self.method_combo.addItem("All")
        for m in sorted(list(unique_methods)):
            self.method_combo.addItem(m)
            
        # 2. Scheme Filter
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItem("All")
        for s in sorted(list(unique_schemes)):
            self.scheme_combo.addItem(s)
            
        # 3. Company ID Filter
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Search by ID...")
        self.company_input.setClearButtonEnabled(True)
            
        # 4. Rank Filter
        self.rank_combo = QComboBox()
        self.rank_combo.addItem("All")
        for r in sorted(list(unique_ranks), key=int):
            self.rank_combo.addItem(r)
            
        # 5. Score Range Filter
        self.min_score_spin = QDoubleSpinBox()
        self.min_score_spin.setRange(-9999.0, 9999.0)
        self.min_score_spin.setValue(-9999.0)
        self.min_score_spin.setDecimals(4)
        
        self.max_score_spin = QDoubleSpinBox()
        self.max_score_spin.setRange(-9999.0, 9999.0)
        self.max_score_spin.setValue(9999.0)
        self.max_score_spin.setDecimals(4)
        
        # Connect signals
        for combo in [self.method_combo, self.scheme_combo, self.rank_combo]:
            combo.currentTextChanged.connect(self._populate_table)
        self.company_input.textChanged.connect(self._populate_table)
        self.min_score_spin.valueChanged.connect(self._populate_table)
        self.max_score_spin.valueChanged.connect(self._populate_table)

        # Build layout
        col1 = QFormLayout()
        col1.addRow("Method:", self.method_combo)
        col1.addRow("Scheme:", self.scheme_combo)
        
        col2 = QFormLayout()
        col2.addRow("Company ID:", self.company_input)
        col2.addRow("Rank:", self.rank_combo)
        
        col3 = QFormLayout()
        col3.addRow("Min Score:", self.min_score_spin)
        col3.addRow("Max Score:", self.max_score_spin)
        
        filter_layout.addLayout(col1)
        filter_layout.addLayout(col2)
        filter_layout.addLayout(col3)
        
        tab_layout.addWidget(filter_group)

        # Create Table Widget
        self.summary_table = QTableWidget()
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.summary_table.setAlternatingRowColors(True)

        tab_layout.addWidget(self.summary_table)
        
        # Export Button
        export_btn_layout = QHBoxLayout()
        export_btn_layout.addStretch()
        self.export_csv_btn = QPushButton("Export Filtered Table to CSV")
        self.export_csv_btn.setProperty("class", "success")
        self.export_csv_btn.style().unpolish(self.export_csv_btn)
        self.export_csv_btn.style().polish(self.export_csv_btn)
        self.export_csv_btn.clicked.connect(self._export_filtered_table)
        export_btn_layout.addWidget(self.export_csv_btn)
        tab_layout.addLayout(export_btn_layout)

        self.results_stack.addWidget(tab)
        
        # Initial population
        self.current_summary_df = pd.DataFrame()
        self._populate_table()

    def _populate_table(self, *args) -> None:
        """Populate the summary table based on the selected method filter."""
        selected_method = self.method_combo.currentText()
        selected_scheme = self.scheme_combo.currentText()
        search_company = self.company_input.text().strip().lower()
        selected_rank = self.rank_combo.currentText()
        min_score = self.min_score_spin.value()
        max_score = self.max_score_spin.value()

        summary_rows = []
        for key, df in self.display_results.items():
            # key looks like AHP_scheme_name
            parts = key.split("_")
            method = parts[0]
            scheme = "_".join(parts[1:])
            
            if selected_method != "All" and method != selected_method:
                continue
            if selected_scheme != "All" and scheme != selected_scheme:
                continue

            # Sort by rank and take top 5
            top_5 = df.nsmallest(5, "Rank")
            for _, row in top_5.iterrows():
                comp_id = str(row["ID"])
                rank = int(row["Rank"])
                score = float(row["Score"])
                
                if search_company and search_company not in comp_id.lower():
                    continue
                if selected_rank != "All" and str(rank) != selected_rank:
                    continue
                if not (min_score <= score <= max_score):
                    continue

                summary_rows.append({
                    "Method": method,
                    "Scheme": scheme,
                    "Rank": rank,
                    "Company ID": comp_id,
                    "Score": score,
                })

        summary_df = pd.DataFrame(summary_rows)
        self.current_summary_df = summary_df # Save for export

        self.summary_table.clear()

        if not summary_df.empty:
            summary_df = summary_df.sort_values(by=["Method", "Scheme", "Rank"]).reset_index(drop=True)
            self.summary_table.setRowCount(len(summary_df))
            self.summary_table.setColumnCount(len(summary_df.columns))
            self.summary_table.setHorizontalHeaderLabels(list(summary_df.columns))

            for row_idx, row in summary_df.iterrows():
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem()
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            item.setData(Qt.ItemDataRole.DisplayRole, f"{value:.4f}")
                        else:
                            item.setData(Qt.ItemDataRole.DisplayRole, value)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    else:
                        item.setText(str(value))
                    self.summary_table.setItem(row_idx, col_idx, item)

            # Auto stretch columns
            header = self.summary_table.horizontalHeader()
            for col in range(len(summary_df.columns)):
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        else:
            self.summary_table.setRowCount(0)
            self.summary_table.setColumnCount(0)

    def _export_filtered_table(self) -> None:
        if self.current_summary_df.empty:
            QMessageBox.information(self, "Export", "No data to export. Adjust filters to find data.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Filtered Results",
            str(self.excel_path.parent / "filtered_results.csv"),
            "CSV Files (*.csv)"
        )
        if file_path:
            try:
                self.current_summary_df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", f"Data exported successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Could not save file:\n{e}")

    def _setup_charts_tab(self) -> None:
        """Set up the visual charts preview tab."""
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(14, 14, 14, 14)
        scroll_layout.setSpacing(20)

        # Iterate over paths and show images
        for path in self.chart_paths:
            if path.exists():
                lbl = QLabel()
                pixmap = QPixmap(str(path))
                
                # Scale pixmap down to fit view width comfortably
                scaled_pixmap = pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation)
                lbl.setPixmap(scaled_pixmap)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                caption = QLabel(f"Chart: {path.name}")
                caption.setProperty("role", "muted")
                caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
                caption.style().unpolish(caption)
                caption.style().polish(caption)

                scroll_layout.addWidget(lbl)
                scroll_layout.addWidget(caption)

        scroll_layout.addStretch()
        scroll_area = make_scroll_area(scroll_widget)
        self.results_stack.addWidget(scroll_area)

    def _setup_export_tab(self) -> None:
        """Set up the spreadsheet exporter launch tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(30, 40, 30, 40)
        tab_layout.setSpacing(20)

        lbl = QLabel("Excel Workbook Successfully Exported")
        lbl.setProperty("role", "subheader")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tab_layout.addWidget(lbl)

        path_lbl = QLabel(f"Location:\n{self.excel_path}")
        path_lbl.setWordWrap(True)
        path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path_lbl.setStyleSheet("font-size: 14pt; color: #555555; background-color: #eef2f3; padding: 12px; border-radius: 6px;")
        tab_layout.addWidget(path_lbl)

        # Buttons to open file or folder
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_file_btn = QPushButton("Open Excel Report")
        open_file_btn.setProperty("class", "success")
        open_file_btn.style().unpolish(open_file_btn)
        open_file_btn.style().polish(open_file_btn)
        open_file_btn.clicked.connect(self.open_excel_file)

        open_dir_btn = QPushButton("Open Folder")
        open_dir_btn.setProperty("class", "secondary")
        open_dir_btn.style().unpolish(open_dir_btn)
        open_dir_btn.style().polish(open_dir_btn)
        open_dir_btn.clicked.connect(self.open_containing_folder)

        btn_layout.addWidget(open_file_btn)
        btn_layout.addWidget(open_dir_btn)
        btn_layout.addStretch()
        tab_layout.addLayout(btn_layout)

        tab_layout.addStretch()
        self.results_stack.addWidget(tab)

    # ── Actions ─────────────────────────────────────────────────────────────

    def open_excel_file(self) -> None:
        """Open the generated Excel document with the default system application."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.excel_path)))

    def open_containing_folder(self) -> None:
        """Open the folder containing the generated Excel workbook."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.excel_path.parent)))
