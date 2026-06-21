"""
company_dialog.py — Dialog for adding, viewing, and removing company records.

Supports both Supplier and Buyer entity types with specialized criteria lists
and validation.
"""

from __future__ import annotations

# stdlib
from typing import Any

# PyQt6
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# third-party
import pandas as pd

# local core
from app.core.company_manager import CompanyManager
from app.core.criteria import CriteriaConfig
# local gui
from app.config import DIMENSIONS
from app.gui.widgets import build_criterion_form, confirm_delete, make_scroll_area


class CompanyManagerDialog(QDialog):
    """Dialog to manage company records (add, view, remove).

    Allows users to toggle scores for the 9 fixed MCDM criteria and validates inputs.
    """

    def __init__(self, entity_type: str, parent: QWidget | None = None) -> None:
        """Initialize the company manager dialog.

        Args:
            entity_type: "supplier" or "buyer".
            parent: Parent widget.
        """
        super().__init__(parent)
        self.entity_type = entity_type.lower()
        self.company_manager = CompanyManager()
        self.criteria_names = CriteriaConfig.get_criteria_names(self.entity_type)

        self.setWindowTitle(f"Manage {entity_type.title()}s")
        self.setFixedSize(DIMENSIONS["dialog_width"], DIMENSIONS["dialog_height"])

        self._setup_ui()
        self.refresh_table()

    def _setup_ui(self) -> None:
        """Set up the layout and widgets of the dialog."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header banner
        header = QLabel(f"{self.entity_type.title()} Directory Management")
        header.setProperty("role", "header")
        layout.addWidget(header)

        # Tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._setup_add_tab()
        self._setup_view_tab()

        # Bottom Close button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(14, 0, 14, 14)
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _setup_add_tab(self) -> None:
        """Set up the 'Add New' tab contents."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(10)

        # Name entry row
        name_layout = QHBoxLayout()
        name_lbl = QLabel("Company Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(f"Enter {self.entity_type} name...")
        self.name_input.setMaximumWidth(400)
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.name_input)
        name_layout.addStretch()
        tab_layout.addLayout(name_layout)

        # Scrollable form for the 9 criteria
        form_widget, self.spin_rows = build_criterion_form(self.criteria_names)
        scroll_area = make_scroll_area(form_widget)
        tab_layout.addWidget(scroll_area)

        # Save Button
        self.save_btn = QPushButton("Save Company")
        self.save_btn.setProperty("class", "success")
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)
        self.save_btn.clicked.connect(self.save_company)
        tab_layout.addWidget(self.save_btn)

        self.tab_widget.addTab(tab, "Add Company")

    def _setup_view_tab(self) -> None:
        """Set up the 'View / Remove' tab contents."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(10)

        # Table Widget
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        tab_layout.addWidget(self.table)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Remove Selected")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.style().unpolish(self.delete_btn)
        self.delete_btn.style().polish(self.delete_btn)
        self.delete_btn.clicked.connect(self.remove_selected_company)

        self.refresh_btn = QPushButton("Refresh Table")
        self.refresh_btn.setProperty("class", "flat")
        self.refresh_btn.style().unpolish(self.refresh_btn)
        self.refresh_btn.style().polish(self.refresh_btn)
        self.refresh_btn.clicked.connect(self.refresh_table)

        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        tab_layout.addLayout(btn_layout)

        self.tab_widget.addTab(tab, "View / Remove")

    # ── Actions & Logics ────────────────────────────────────────────────────

    def save_company(self) -> None:
        """Save the new company record to disk."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Company name cannot be empty.")
            return

        scores = {row.label_text(): row.value() for row in self.spin_rows}

        try:
            self.company_manager.add_company(self.entity_type, name, scores)
            QMessageBox.information(
                self,
                "Success",
                f"{self.entity_type.title()} '{name}' has been saved successfully.",
            )
            # Reset form
            self.name_input.clear()
            for row in self.spin_rows:
                row.reset()
            # Refresh directory view
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save company: {e}")

    def refresh_table(self) -> None:
        """Reload companies from the data folder and populate the table."""
        try:
            df = self.company_manager.load_all_as_dataframe(self.entity_type)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load companies: {e}")
            return

        if df.empty:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns) + 1)
        
        # Wrap criteria headers to avoid clipping at large font sizes
        import textwrap
        wrapped_headers = ["Select"]
        for col in df.columns:
            if col == "ID":
                wrapped_headers.append("Company Name")  # "ID" is actually the Company Name
            else:
                wrapped_headers.append("\n".join(textwrap.wrap(col, 15)))
        self.table.setHorizontalHeaderLabels(wrapped_headers)

        # Fill table data
        for row_idx, row in df.iterrows():
            # Checkbox column at index 0
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row_idx, 0, chk_item)

            for col_idx, value in enumerate(row):
                item = QTableWidgetItem()
                if isinstance(value, (int, float)):
                    item.setData(Qt.ItemDataRole.DisplayRole, value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setText(str(value))
                self.table.setItem(row_idx, col_idx + 1, item)

        # Style headers & make columns non-resizable by user
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Force layout recalculation and adjust dialog size to fit table exactly
        self.table.resizeColumnsToContents()
        table_width = 0
        for col in range(self.table.columnCount()):
            table_width += self.table.columnWidth(col)
            
        # Update dialog to exactly the width needed for all columns
        dialog_width = max(DIMENSIONS["dialog_width"], table_width + 80)
        self.setFixedSize(dialog_width, DIMENSIONS["dialog_height"])

    def remove_selected_company(self) -> None:
        """Remove the selected company or checked companies from the data storage."""
        # Find all checked companies
        checked_companies = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                comp_name_item = self.table.item(row, 1)
                if comp_name_item:
                    checked_companies.append(comp_name_item.text())

        # Fallback to selected row if no check boxes are ticked
        if not checked_companies:
            selected_ranges = self.table.selectedRanges()
            if selected_ranges:
                row = selected_ranges[0].topRow()
                comp_name_item = self.table.item(row, 1)
                if comp_name_item:
                    checked_companies.append(comp_name_item.text())

        if not checked_companies:
            QMessageBox.warning(self, "Selection Error", "Please check or select at least one company to remove.")
            return

        # Confirm deletion of selected companies
        if len(checked_companies) == 1:
            msg = f'Are you sure you want to delete "{checked_companies[0]}"?\n\nThis action cannot be undone.'
        else:
            msg = f'Are you sure you want to delete {len(checked_companies)} selected companies?\n\nThis action cannot be undone.'

        answer = QMessageBox.question(
            self,
            "Confirm Delete",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            failed = []
            for comp_name in checked_companies:
                try:
                    self.company_manager.remove_company(self.entity_type, comp_name)
                except Exception as e:
                    failed.append(f"{comp_name}: {e}")

            if failed:
                QMessageBox.critical(self, "Error", "Could not delete some companies:\n" + "\n".join(failed))
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully removed {len(checked_companies)} company record(s)." if len(checked_companies) > 1 else f"Company '{checked_companies[0]}' has been removed."
                )
            self.refresh_table()
