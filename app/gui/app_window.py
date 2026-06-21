"""
app_window.py — Main Window dashboard that orchestrates launcher buttons and updates dashboard metrics.
"""

from __future__ import annotations

# stdlib
from typing import Any, Callable

# PyQt6
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# local core
from app.core.company_manager import CompanyManager
from app.core.weight_manager import WeightSchemeManager
# local gui
from app.config import DIMENSIONS, COLORS
from app.gui.analyzer_dialog import DecisionAnalyzer
from app.gui.company_dialog import CompanyManagerDialog
from app.gui.dataset_dialog import DatasetGenerationDialog
from app.gui.weight_dialog import WeightSchemeDialog


class MainWindow(QMainWindow):
    """Main dashboard interface window for the MCDM Decision Support System.

    Coordinates launching sub-dialogs for the selected role and running analysis solvers,
    dynamically updating dashboard statistics on return.
    """

    def __init__(self, role: str, on_switch_role: Callable[[], None]) -> None:
        """Initialize the main application dashboard.

        Args:
            role: "buyer" or "supplier"
            on_switch_role: callback to execute when user wants to switch role.
        """
        super().__init__()
        self.role = role.lower()
        self.on_switch_role = on_switch_role
        
        self.company_manager = CompanyManager()
        self.weight_manager = WeightSchemeManager()

        self.setWindowTitle("MCDM Decision Support System")
        self.resize(DIMENSIONS["main_width"], DIMENSIONS["main_height"])

        self._setup_ui()
        self.refresh_dashboard_metrics()

    def _setup_ui(self) -> None:
        """Set up the layout and widgets of the main window for the active role."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Header banner area
        header_container = QWidget()
        # Set dynamic background color based on role
        accent_color = COLORS.get(f"{self.role}_accent", COLORS["primary"])
        header_container.setStyleSheet(f"background-color: {accent_color};")
        
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(DIMENSIONS["pad"], DIMENSIONS["pad"], DIMENSIONS["pad"], DIMENSIONS["pad"])
        
        role_title = self.role.title()
        header = QLabel(f"MCDM Analysis System — {role_title} Portal")
        header.setStyleSheet("color: white; font-size: 24pt; font-family: 'Segoe UI'; font-weight: 600;")
        
        # Switch Role Button
        switch_btn = QPushButton("Switch Role")
        switch_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14pt;
                font-weight: bold;
            }
            QLabel {
                color: #ffffff;
                font-size: 14pt;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        switch_btn.clicked.connect(self._handle_switch_role)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(switch_btn)
        
        main_layout.addWidget(header_container)

        # Subtitle
        subtitle_container = QWidget()
        subtitle_layout = QVBoxLayout(subtitle_container)
        subtitle_layout.setContentsMargins(20, 0, 20, 0)
        subtitle = QLabel(f"Bidirectional Evaluation Platform utilizing AHP, TOPSIS, and VIKOR Solvers ({role_title} Perspective)")
        subtitle.setProperty("role", "subheader")
        subtitle_layout.addWidget(subtitle)
        main_layout.addWidget(subtitle_container)

        # Main Panel
        panel_container = QWidget()
        panel_container.setContentsMargins(20, 0, 20, 0)
        panel_layout = QVBoxLayout(panel_container)
        panel_layout.setSpacing(20)

        self.role_card = QFrame()
        self.role_card.setProperty("role", "card")
        self.role_card.style().unpolish(self.role_card)
        self.role_card.style().polish(self.role_card)
        
        card_layout = QVBoxLayout(self.role_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(16)

        card_title = QLabel(f"{role_title} Analysis Portal")
        title_color = accent_color
        card_title.setStyleSheet(f"font-size: 28pt; font-weight: bold; color: {title_color};")
        card_layout.addWidget(card_title)

        # Metrics layout
        metrics = QGridLayout()
        metrics.setSpacing(20)
        metrics.addWidget(QLabel(f"Registered {role_title}s:"), 0, 0)
        self.count_lbl = QLabel("0")
        self.count_lbl.setStyleSheet("font-weight: bold; font-size: 28pt;")
        metrics.addWidget(self.count_lbl, 0, 1)

        metrics.addWidget(QLabel("Weight Schemes:"), 1, 0)
        self.schemes_lbl = QLabel("0")
        self.schemes_lbl.setStyleSheet("font-weight: bold; font-size: 28pt;")
        metrics.addWidget(self.schemes_lbl, 1, 1)
        card_layout.addLayout(metrics)

        # Actions
        manage_btn = QPushButton(f"Manage {role_title} Profiles")
        manage_btn.clicked.connect(self.open_company_manager)
        
        weights_btn = QPushButton("Manage Weight Schemes")
        weights_btn.clicked.connect(self.open_weight_manager)
        
        gen_btn = QPushButton("Generate Synthetic Data")
        gen_btn.clicked.connect(self.open_dataset_generator)
        gen_btn.setProperty("class", "flat")
        gen_btn.style().unpolish(gen_btn)
        gen_btn.style().polish(gen_btn)

        card_layout.addWidget(manage_btn)
        card_layout.addWidget(weights_btn)
        card_layout.addWidget(gen_btn)
        card_layout.addStretch()

        panel_layout.addWidget(self.role_card)
        main_layout.addWidget(panel_container)

        main_layout.addStretch()

        # Run Solver Highlight Bar at the bottom
        solver_bar = QWidget()
        solver_bar.setContentsMargins(20, 0, 20, 20)
        solver_layout = QHBoxLayout(solver_bar)
        solver_layout.setContentsMargins(0, 0, 0, 0)

        run_solver_btn = QPushButton("Launch Decision Analyzer")
        run_solver_btn.setProperty("class", "success")
        run_solver_btn.style().unpolish(run_solver_btn)
        run_solver_btn.style().polish(run_solver_btn)
        run_solver_btn.setMinimumHeight(44)
        run_solver_btn.clicked.connect(self.launch_solver)
        
        solver_layout.addWidget(run_solver_btn)
        main_layout.addWidget(solver_bar)
        
    def _handle_switch_role(self) -> None:
        """Prompt confirmation and invoke the switch role callback."""
        answer = QMessageBox.question(
            self,
            "Switch Role",
            "Switch role? Any unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.on_switch_role()

    # ── Refresh Metrics ─────────────────────────────────────────────────────

    def refresh_dashboard_metrics(self) -> None:
        """Query storage directories and update metrics text labels."""
        try:
            count = len(self.company_manager.list_companies(self.role))
            schemes = len(self.weight_manager.list_schemes(self.role))
            self.count_lbl.setText(str(count))
            self.schemes_lbl.setText(str(schemes))
        except Exception:
            pass

    # ── Action Handlers ─────────────────────────────────────────────────────

    def open_company_manager(self) -> None:
        """Launch the company manager dialog modal."""
        dialog = CompanyManagerDialog(self.role, self)
        dialog.exec()
        self.refresh_dashboard_metrics()

    def open_weight_manager(self) -> None:
        """Launch the weight scheme manager dialog modal."""
        dialog = WeightSchemeDialog(self.role, self)
        dialog.exec()
        self.refresh_dashboard_metrics()

    def open_dataset_generator(self) -> None:
        """Launch the synthetic dataset generator dialog modal."""
        dialog = DatasetGenerationDialog(self.role, self)
        dialog.exec()
        self.refresh_dashboard_metrics()

    def launch_solver(self) -> None:
        """Launch the decision analyzer dialog modal."""
        dialog = DecisionAnalyzer(self.role, self)
        dialog.exec()
        self.refresh_dashboard_metrics()
