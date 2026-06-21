"""
analyzer_dialog.py — Dialog for selecting weight schemes, methods, and running MCDM analysis.

Spawns background computations and displays ResultsViewWidget on success.
"""

from __future__ import annotations

# stdlib
from pathlib import Path

# PyQt6
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# third-party
import pandas as pd

# local core
from app.core.company_manager import CompanyManager
from app.core.dataset_generator import DatasetGenerator
from app.core.weight_manager import WeightSchemeManager
# local gui
from app.config import DIMENSIONS, COLORS
from app.gui.widgets import HorizontalLine, make_scroll_area, make_status_label
from app.gui.workers import AnalysisWorker


class DataPreviewDialog(QDialog):
    """Modeless dialog to preview the first 10 rows of the selected dataset."""
    def __init__(self, df: pd.DataFrame, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Data Preview (Top 10 Rows)")
        self.setMinimumSize(800, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        if not df.empty:
            table.setRowCount(len(df))
            table.setColumnCount(len(df.columns))
            table.setHorizontalHeaderLabels(list(df.columns))
            
            for row_idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    table.setItem(row_idx, col_idx, item)
                    
            header = table.horizontalHeader()
            for col in range(len(df.columns)):
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
                
        layout.addWidget(table)
        
        close_btn = QPushButton("Close Preview")
        close_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)


class DecisionAnalyzer(QDialog):
    """Dialog to configure and execute AHP, TOPSIS, and VIKOR evaluations.

    The DecisionAnalyzer serves as the analytical engine interface for multi-criteria
    decision analysis, consistent with academic terminology used in MCDM literature.
    Runs solvers in the background using AnalysisWorker and forwards results
    to the ResultsViewWidget.
    """

    def __init__(self, role: str, parent: QWidget | None = None) -> None:
        """Initialize the decision analyzer dialog.

        Args:
            role: "buyer" or "supplier"
            parent: Parent widget.
        """
        super().__init__(parent)
        self.role = role.lower()
        self.company_manager = CompanyManager()
        self.weight_manager = WeightSchemeManager()
        self.dataset_generator = DatasetGenerator()
        self.worker: AnalysisWorker | None = None
        self.results_page: QWidget | None = None

        role_title = self.role.title()
        self.setWindowTitle(f"Decision Analyzer — {role_title} Evaluation")
        self.setFixedSize(DIMENSIONS["dialog_width"], DIMENSIONS["dialog_height"] + 60)

        self._setup_ui()
        self.on_data_source_changed()
        self.on_role_initialized()

    def _setup_ui(self) -> None:
        """Set up the stacked layout and widgets of the dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget(self)
        layout.addWidget(self.stacked_widget)
        
        # ─── Page 0: Analyzer Form ───
        self.analyzer_page = QWidget()
        analyzer_layout = QVBoxLayout(self.analyzer_page)
        analyzer_layout.setContentsMargins(0, 0, 0, 0)
        analyzer_layout.setSpacing(10)

        # Header banner
        header = QLabel("Decision Analyzer")
        header.setProperty("role", "header")
        analyzer_layout.addWidget(header)

        # Main Scrollable settings form
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(16)

        # Role Label
        role_title = self.role.title()
        accent_color = COLORS.get(f"{self.role}_accent", COLORS["primary"])
        
        role_lbl = QLabel(f"Analyzing: {role_title}")
        role_lbl.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {accent_color};")
        scroll_layout.addWidget(role_lbl)

        scroll_layout.addWidget(HorizontalLine())

        # Select Data Source
        step2_title = QLabel("Select Data Source")
        step2_title.setProperty("role", "subheader")
        scroll_layout.addWidget(step2_title)

        source_widget = QWidget()
        source_layout = QHBoxLayout(source_widget)
        source_layout.setContentsMargins(0, 0, 0, 0)
        self.source_group = QButtonGroup(self)
        self.real_radio = QRadioButton("Real Companies")
        self.gen_radio = QRadioButton("Generated Dataset")
        self.real_radio.setChecked(True)
        self.source_group.addButton(self.real_radio)
        self.source_group.addButton(self.gen_radio)
        
        self.preview_btn = QPushButton("Preview Data")
        self.preview_btn.setProperty("class", "secondary")
        self.preview_btn.style().unpolish(self.preview_btn)
        self.preview_btn.style().polish(self.preview_btn)
        self.preview_btn.clicked.connect(self._show_data_preview)
        
        source_layout.addWidget(self.real_radio)
        source_layout.addWidget(self.gen_radio)
        source_layout.addStretch()
        source_layout.addWidget(self.preview_btn)
        scroll_layout.addWidget(source_widget)

        self.real_radio.toggled.connect(self.on_data_source_changed)

        self.source_status = make_status_label("Checking data source...", "neutral")
        scroll_layout.addWidget(self.source_status)

        scroll_layout.addWidget(HorizontalLine())

        # Select Weight Schemes
        step3_title = QLabel("Select Weight Schemes")
        step3_title.setProperty("role", "subheader")
        scroll_layout.addWidget(step3_title)

        self.schemes_list = QListWidget()
        self.schemes_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.schemes_list.setMinimumHeight(100)
        scroll_layout.addWidget(self.schemes_list)

        scroll_layout.addWidget(HorizontalLine())

        # Select MCDM Methods
        step4_title = QLabel("Select MCDM Methods")
        step4_title.setProperty("role", "subheader")
        scroll_layout.addWidget(step4_title)

        methods_widget = QWidget()
        methods_layout = QHBoxLayout(methods_widget)
        methods_layout.setContentsMargins(0, 0, 0, 0)
        methods_layout.setSpacing(20)
        self.ahp_chk = QCheckBox("AHP (Analytical Hierarchy Process)")
        self.topsis_chk = QCheckBox("TOPSIS (Ideal Solution Distance)")
        self.vikor_chk = QCheckBox("VIKOR (Compromise Ranking)")
        self.ahp_chk.setChecked(True)
        self.topsis_chk.setChecked(True)
        self.vikor_chk.setChecked(True)
        methods_layout.addWidget(self.ahp_chk)
        methods_layout.addWidget(self.topsis_chk)
        methods_layout.addWidget(self.vikor_chk)
        methods_layout.addStretch()
        scroll_layout.addWidget(methods_widget)

        self.vikor_chk.toggled.connect(self.on_vikor_toggled)

        # Step 5: VIKOR Parameter
        self.vikor_groupbox = QFrame()
        self.vikor_groupbox.setProperty("role", "card")
        self.vikor_groupbox.style().unpolish(self.vikor_groupbox)
        self.vikor_groupbox.style().polish(self.vikor_groupbox)
        
        v_layout = QVBoxLayout(self.vikor_groupbox)
        v_layout.setContentsMargins(10, 10, 10, 10)
        
        v_title = QLabel("VIKOR v Parameter")
        v_title.setProperty("role", "muted")
        v_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(v_title)

        input_layout = QHBoxLayout()
        self.v_spin = QDoubleSpinBox()
        self.v_spin.setRange(0.0, 1.0)
        self.v_spin.setSingleStep(0.05)
        self.v_spin.setDecimals(2)
        self.v_spin.setValue(0.50)
        self.v_spin.setFixedWidth(120)
        
        self.v_warning_lbl = QLabel("")
        self.v_warning_lbl.setStyleSheet("color: red; font-size: 11pt;")
        
        input_layout.addStretch()
        input_layout.addWidget(self.v_spin)
        input_layout.addWidget(self.v_warning_lbl)
        input_layout.addStretch()
        v_layout.addLayout(input_layout)

        # Guidance labels
        guide_layout = QHBoxLayout()
        guide_layout.addWidget(QLabel("0.0 Regret-averse"))
        guide_layout.addStretch()
        guide_layout.addWidget(QLabel("0.5 Balanced"))
        guide_layout.addStretch()
        guide_layout.addWidget(QLabel("1.0 Utility-focused"))
        v_layout.addLayout(guide_layout)
        
        self.v_spin.lineEdit().textEdited.connect(self._validate_v_input)
        scroll_layout.addWidget(self.vikor_groupbox)

        analyzer_layout.addWidget(make_scroll_area(scroll_widget))

        # Bottom Actions Layout
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(14, 0, 14, 14)
        bottom_layout.setSpacing(10)

        self.status_lbl = make_status_label("Configure solver parameters and run.", "neutral")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        
        self.run_btn = QPushButton("Run MCDM Analysis")
        self.run_btn.setProperty("class", "success")
        self.run_btn.style().unpolish(self.run_btn)
        self.run_btn.style().polish(self.run_btn)
        self.run_btn.clicked.connect(self.start_analysis)

        # Close row
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        close_row.addWidget(close_btn)

        bottom_layout.addWidget(self.status_lbl)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.run_btn)
        bottom_layout.addLayout(close_row)
        analyzer_layout.addWidget(bottom_container)
        
        self.stacked_widget.addWidget(self.analyzer_page)

    # ── State Toggles ───────────────────────────────────────────────────────

    def on_role_initialized(self) -> None:
        """Update weight schemes list on initialization."""
        entity_type = self.role

        # Update weight schemes list
        self.schemes_list.clear()
        try:
            schemes = self.weight_manager.list_schemes(entity_type)
            if not schemes:
                item = QListWidgetItem("No weight schemes found. Please create one first.")
                item.setForeground(Qt.GlobalColor.red)
                self.schemes_list.addItem(item)
                self.run_btn.setEnabled(False)
            else:
                for scheme in schemes:
                    item = QListWidgetItem(scheme)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Checked)  # check by default
                    self.schemes_list.addItem(item)
                
                # Dynamically size the list height based on count of schemes to show them all clearly
                count = self.schemes_list.count()
                row_height = 48  # Approximate height per list item for 17pt font with padding
                self.schemes_list.setFixedHeight(max(120, count * row_height + 8))
        except Exception:
            pass

        self.on_data_source_changed()

    def on_data_source_changed(self) -> None:
        """Verify existence of selected data source and display warnings if missing."""
        entity_type = self.role
        is_real = self.real_radio.isChecked()

        self.run_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)

        if is_real:
            companies = self.company_manager.list_companies(entity_type)
            count = len(companies)
            if count == 0:
                self.source_status.setText(f"No stored {entity_type}s found. Run Manage Companies first.")
                self.source_status.setProperty("status", "error")
                self.run_btn.setEnabled(False)
                self.preview_btn.setEnabled(False)
            else:
                self.source_status.setText(f"Found {count} registered {entity_type}(s).")
                self.source_status.setProperty("status", "success")
        else:
            dataset_path = self.dataset_generator._dataset_path(entity_type)
            if not dataset_path.exists():
                self.source_status.setText(f"No generated {entity_type} CSV dataset file found. Run Generate Test Data first.")
                self.source_status.setProperty("status", "error")
                self.run_btn.setEnabled(False)
                self.preview_btn.setEnabled(False)
            else:
                try:
                    df = pd.read_csv(dataset_path)
                    self.source_status.setText(f"Dataset file exists: {len(df)} records found.")
                    self.source_status.setProperty("status", "success")
                except Exception as e:
                    self.source_status.setText(f"Error loading dataset CSV: {e}")
                    self.source_status.setProperty("status", "error")
                    self.run_btn.setEnabled(False)
                    self.preview_btn.setEnabled(False)

        self.source_status.style().unpolish(self.source_status)
        self.source_status.style().polish(self.source_status)

    def _show_data_preview(self) -> None:
        """Show modal preview of the active dataset."""
        entity_type = self.role
        try:
            if self.real_radio.isChecked():
                df = self.company_manager.load_all_as_dataframe(entity_type)
            else:
                dataset_path = self.dataset_generator._dataset_path(entity_type)
                df = pd.read_csv(dataset_path)
            
            if df.empty:
                QMessageBox.information(self, "Preview", "No data available to preview.")
                return
            
            # Show top 10 rows
            preview_df = df.head(10)
            dialog = DataPreviewDialog(preview_df, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Failed to load preview: {e}")

    def on_vikor_toggled(self, checked: bool) -> None:
        """Show or hide the VIKOR parameter editing section.

        Args:
            checked: True if VIKOR checkbox is selected.
        """
        self.vikor_groupbox.setVisible(checked)

    def _validate_v_input(self, text: str) -> None:
        """Show warning if user types outside 0.0 - 1.0 range."""
        try:
            val = float(text)
            if val < 0.0 or val > 1.0:
                self.v_warning_lbl.setText("Value must be between 0.0 and 1.0 (will be clamped)")
            else:
                self.v_warning_lbl.setText("")
        except ValueError:
            self.v_warning_lbl.setText("")

    # ── Executing Solver ────────────────────────────────────────────────────

    def start_analysis(self) -> None:
        """Initiate background solver computations after verifying choices."""
        entity_type = self.role

        # Get selected schemes
        selected_schemes = []
        for i in range(self.schemes_list.count()):
            item = self.schemes_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_schemes.append(item.text())

        if not selected_schemes:
            QMessageBox.warning(self, "Configuration Error", "Please select at least one weight scheme.")
            return

        # Get selected methods
        methods = []
        if self.ahp_chk.isChecked():
            methods.append("AHP")
        if self.topsis_chk.isChecked():
            methods.append("TOPSIS")
        if self.vikor_chk.isChecked():
            methods.append("VIKOR")

        if not methods:
            QMessageBox.warning(self, "Configuration Error", "Please select at least one MCDM method.")
            return

        # Retrieve proper dataframe
        if self.real_radio.isChecked():
            scores_df = self.company_manager.load_all_as_dataframe(entity_type)
        else:
            dataset_path = self.dataset_generator._dataset_path(entity_type)
            scores_df = pd.read_csv(dataset_path)

        # Get v value
        v_param = self.v_spin.value()

        # Lock UI & show progress bar
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setText("Running background calculations, producing charts & Excel report...")
        self.status_lbl.setProperty("status", "neutral")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        # Spawn worker
        self.worker = AnalysisWorker(
            entity_type, scores_df, selected_schemes, methods, v_param, self
        )
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    def set_ui_enabled(self, enabled: bool) -> None:
        """Enable or disable dialog input controls to prevent double clicks during execution.

        Args:
            enabled: True to enable inputs.
        """
        self.real_radio.setEnabled(enabled)
        self.gen_radio.setEnabled(enabled)
        self.schemes_list.setEnabled(enabled)
        self.ahp_chk.setEnabled(enabled)
        self.topsis_chk.setEnabled(enabled)
        self.vikor_chk.setEnabled(enabled)
        self.vikor_groupbox.setEnabled(enabled and self.vikor_chk.isChecked())
        self.run_btn.setEnabled(enabled)

    def on_analysis_finished(
        self,
        display_results: dict[str, pd.DataFrame],
        chart_paths: list[Path],
        excel_path: Path,
    ) -> None:
        """Hide analyzer, switch to embedded ResultsViewWidget.

        Args:
            display_results: Method-scheme mapped score frames.
            chart_paths: Generated chart location references.
            excel_path: Generated spreadsheet path reference.
        """
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_lbl.setText("Analysis completed successfully!")
        self.status_lbl.setProperty("status", "success")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        # Clear old results page if it exists
        if self.results_page:
            self.stacked_widget.removeWidget(self.results_page)
            self.results_page.deleteLater()
            self.results_page = None

        from app.gui.results_viewer import ResultsViewWidget
        self.results_page = ResultsViewWidget(
            entity_type=self.role,
            display_results=display_results,
            chart_paths=chart_paths,
            excel_path=excel_path,
        )
        self.results_page.back_btn.clicked.connect(self.show_analyzer_page)
        
        self.stacked_widget.addWidget(self.results_page)
        self.stacked_widget.setCurrentWidget(self.results_page)

    def show_analyzer_page(self) -> None:
        """Switch stacked layout back to analyzer configuration form."""
        self.stacked_widget.setCurrentWidget(self.analyzer_page)

    def on_analysis_error(self, error_msg: str) -> None:
        """Re-enable UI and pop error information dialog.

        Args:
            error_msg: Failure details.
        """
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_lbl.setText("Solver execution failed.")
        self.status_lbl.setProperty("status", "error")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        QMessageBox.critical(self, "Solver Error", f"MCDM analysis failed:\n{error_msg}")
