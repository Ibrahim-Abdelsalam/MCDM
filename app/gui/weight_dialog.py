"""
weight_dialog.py — Dialog for creating, viewing, and deleting weight schemes.

Provides live normalized percentage previews as the user edits weight values.
"""

from __future__ import annotations

# stdlib
from typing import Any

# PyQt6
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# local core
from app.core.criteria import CriteriaConfig
from app.core.weight_manager import WeightSchemeManager
# local gui
from app.config import DIMENSIONS
from app.gui.widgets import confirm_delete, make_scroll_area


class WeightSpinRow(QWidget):
    """Row widget representing a single criterion weight input using QDoubleSpinBox.

    Signals:
        valueChanged (float): Emitted when the spinbox value is changed.
    """

    valueChanged: pyqtSignal = pyqtSignal(float)

    def __init__(
        self,
        label_text: str,
        min_val: float = 0.0,
        max_val: float = 100.0,
        default: float = 1.0,
        step: float = 0.1,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the weight spin row.

        Args:
            label_text: Criterion name.
            min_val: Minimum weight value.
            max_val: Maximum weight value.
            default: Initial value.
            step: Increment step.
            parent: Parent widget.
        """
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        # Label
        self._label = QLabel(label_text)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(self._label)

        # Double Spin Box
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setSingleStep(step)
        self.spinbox.setValue(default)
        self.spinbox.setFixedWidth(80)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinbox)

        # Connect signal
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

    def value(self) -> float:
        """Return the current weight value."""
        return self.spinbox.value()

    def set_value(self, v: float) -> None:
        """Set the weight value programmatically."""
        self.spinbox.setValue(v)

    def reset(self) -> None:
        """Reset the weight value to default (1.0)."""
        self.spinbox.setValue(1.0)

    def label_text(self) -> str:
        """Return the criterion label text."""
        return self._label.text()


class WeightSchemeDialog(QDialog):
    """Dialog to manage criteria weight profiles.

    Includes a live normalization display indicating how weight inputs
    influence total distribution ratios.
    """

    def __init__(self, entity_type: str, parent: QWidget | None = None) -> None:
        """Initialize the weight scheme manager dialog.

        Args:
            entity_type: "supplier" or "buyer".
            parent: Parent widget.
        """
        super().__init__(parent)
        self.entity_type = entity_type.lower()
        self.weight_manager = WeightSchemeManager()
        self.criteria_names = CriteriaConfig.get_criteria_names(self.entity_type)

        self.setWindowTitle(f"Manage {entity_type.title()} Weight Schemes")
        self.setFixedSize(DIMENSIONS["dialog_width"] + 100, DIMENSIONS["dialog_height"])

        self._setup_ui()
        self.refresh_schemes_list()

    def _setup_ui(self) -> None:
        """Set up the overall dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Header banner
        header = QLabel(f"{self.entity_type.title()} Weight Management")
        header.setProperty("role", "header")
        layout.addWidget(header)

        # Tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self._setup_create_tab()
        self._setup_view_tab()

        # Bottom Close button
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(14, 0, 14, 14)
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _setup_create_tab(self) -> None:
        """Set up the 'Create Scheme' tab layout."""
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(14)

        # Left Column: Inputs
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Scheme Name
        name_layout = QHBoxLayout()
        name_lbl = QLabel("Scheme Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Quality Focused, Cost Focused...")
        self.name_input.setMaximumWidth(400)
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.name_input)
        name_layout.addStretch()
        left_layout.addLayout(name_layout)

        # Scrollable form for editing weight values
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(4, 4, 4, 4)
        form_layout.setSpacing(2)

        self.spin_rows: list[WeightSpinRow] = []
        for name in self.criteria_names:
            row = WeightSpinRow(name, min_val=0.0, max_val=100.0, default=1.0)
            row.valueChanged.connect(self.update_preview)
            form_layout.addWidget(row)
            self.spin_rows.append(row)

        form_layout.addStretch()
        scroll_area = make_scroll_area(form_container)
        left_layout.addWidget(scroll_area)

        # Save Button
        self.save_btn = QPushButton("Save Weight Scheme")
        self.save_btn.setProperty("class", "success")
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)
        self.save_btn.clicked.connect(self.save_scheme)
        left_layout.addWidget(self.save_btn)

        tab_layout.addWidget(left_pane, 3)

        # Right Column: Normalized Preview Card
        right_pane = QFrame()
        right_pane.setProperty("role", "card")
        right_pane.style().unpolish(right_pane)
        right_pane.style().polish(right_pane)
        
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        preview_title = QLabel("Normalized Ratios Preview")
        preview_title.setProperty("role", "subheader")
        preview_title.style().unpolish(preview_title)
        preview_title.style().polish(preview_title)
        right_layout.addWidget(preview_title)

        self.preview_text = QTextBrowser()
        self.preview_text.setFrameShape(QFrame.Shape.NoFrame)
        self.preview_text.setOpenExternalLinks(False)
        right_layout.addWidget(self.preview_text)

        tab_layout.addWidget(right_pane, 2)

        self.tab_widget.addTab(tab, "Create Scheme")
        self.update_preview()

    def _setup_view_tab(self) -> None:
        """Set up the 'View / Delete' tab layout."""
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(14)

        # Left Column: Schemes List
        list_pane = QWidget()
        list_layout = QVBoxLayout(list_pane)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(10)

        self.schemes_list = QListWidget()
        self.schemes_list.currentItemChanged.connect(self.show_scheme_details)
        list_layout.addWidget(self.schemes_list)

        # Actions Row
        action_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.style().unpolish(self.delete_btn)
        self.delete_btn.style().polish(self.delete_btn)
        self.delete_btn.clicked.connect(self.delete_selected_scheme)

        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.setProperty("class", "flat")
        self.refresh_btn.style().unpolish(self.refresh_btn)
        self.refresh_btn.style().polish(self.refresh_btn)
        self.refresh_btn.clicked.connect(self.refresh_schemes_list)

        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()
        action_layout.addWidget(self.refresh_btn)
        list_layout.addLayout(action_layout)

        tab_layout.addWidget(list_pane, 3)

        # Right Column: Details Card
        details_pane = QFrame()
        details_pane.setProperty("role", "card")
        details_pane.style().unpolish(details_pane)
        details_pane.style().polish(details_pane)
        
        details_layout = QVBoxLayout(details_pane)
        details_layout.setContentsMargins(10, 10, 10, 10)

        details_title = QLabel("Scheme Weights Profile")
        details_title.setProperty("role", "subheader")
        details_title.style().unpolish(details_title)
        details_title.style().polish(details_title)
        details_layout.addWidget(details_title)

        self.details_text = QTextBrowser()
        self.details_text.setFrameShape(QFrame.Shape.NoFrame)
        details_layout.addWidget(self.details_text)

        tab_layout.addWidget(details_pane, 2)

        self.tab_widget.addTab(tab, "View / Delete")

    # ── Logics & Events ─────────────────────────────────────────────────────

    def update_preview(self) -> None:
        """Calculate and display the normalized percentages preview."""
        weights = {row.label_text(): row.value() for row in self.spin_rows}
        total_weight = sum(weights.values())

        if total_weight <= 0:
            self.preview_text.setHtml("<p style='color: gray;'>Total weight is zero. Add weight values to preview ratios.</p>")
            return

        html_lines = ["<ul style='margin-left: -15px; line-height: 1.4;'>"]
        for name, w in weights.items():
            percentage = (w / total_weight) * 100
            html_lines.append(f"<li><b>{name}:</b> {percentage:.1f}%</li>")
        html_lines.append("</ul>")

        self.preview_text.setHtml("".join(html_lines))

    def save_scheme(self) -> None:
        """Save the new weight scheme."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Weight scheme name cannot be empty.")
            return

        weights = {row.label_text(): row.value() for row in self.spin_rows}
        total_weight = sum(weights.values())

        if total_weight <= 0:
            QMessageBox.warning(self, "Validation Error", "The sum of all weights must be greater than zero.")
            return

        try:
            self.weight_manager.save_scheme(self.entity_type, name, weights)
            QMessageBox.information(
                self,
                "Success",
                f"Weight scheme '{name}' saved successfully.",
            )
            # Reset
            self.name_input.clear()
            for row in self.spin_rows:
                row.reset()
            self.update_preview()
            self.refresh_schemes_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save weight scheme: {e}")

    def refresh_schemes_list(self) -> None:
        """Reload and list saved weight scheme profiles with checkable items."""
        self.schemes_list.clear()
        self.details_text.clear()
        try:
            schemes = self.weight_manager.list_schemes(self.entity_type)
            for s in schemes:
                item = QListWidgetItem(s)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.schemes_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list schemes: {e}")

    def show_scheme_details(self) -> None:
        """Show raw details of the selected weight scheme on the details pane."""
        current_item = self.schemes_list.currentItem()
        if not current_item:
            self.details_text.clear()
            return

        scheme_name = current_item.text()
        try:
            # Load the normalized weights
            norm_weights = self.weight_manager.load_scheme(self.entity_type, scheme_name)
            # Load raw weights from file directory to show exact numbers
            raw_scheme_path = self.weight_manager._find_scheme_file(self.entity_type, scheme_name)
            
            raw_weights = {}
            if raw_scheme_path and raw_scheme_path.exists():
                with open(raw_scheme_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    raw_weights = raw_data.get("weights", {})

            html_lines = [f"<p><b>Scheme Name:</b> {scheme_name}</p><hr/>"]
            html_lines.append("<table width='100%' cellpadding='3' cellspacing='0'>")
            html_lines.append("<tr><th>Criterion</th><th align='right'>Raw</th><th align='right'>Ratio</th></tr>")
            
            for name in self.criteria_names:
                raw_w = raw_weights.get(name, 1.0)
                norm_w = norm_weights.get(name, 0.0)
                html_lines.append(
                    f"<tr><td>{name}</td><td align='right'>{raw_w:.1f}</td><td align='right'>{norm_w * 100:.1f}%</td></tr>"
                )
            html_lines.append("</table>")
            
            self.details_text.setHtml("".join(html_lines))
        except Exception as e:
            self.details_text.setPlainText(f"Error loading scheme details:\n{e}")

    def delete_selected_scheme(self) -> None:
        """Delete the selected weight scheme profile(s)."""
        # Find all checked schemes
        checked_schemes = []
        for index in range(self.schemes_list.count()):
            item = self.schemes_list.item(index)
            if item and item.checkState() == Qt.CheckState.Checked:
                checked_schemes.append(item.text())

        # Fallback to current item if nothing is checked
        if not checked_schemes:
            current_item = self.schemes_list.currentItem()
            if current_item:
                checked_schemes.append(current_item.text())

        if not checked_schemes:
            QMessageBox.warning(self, "Selection Error", "Please check or select at least one scheme to delete.")
            return

        # Confirm delete
        if len(checked_schemes) == 1:
            msg = f'Are you sure you want to delete weight scheme "{checked_schemes[0]}"?\n\nThis action cannot be undone.'
        else:
            msg = f'Are you sure you want to delete {len(checked_schemes)} selected weight schemes?\n\nThis action cannot be undone.'

        answer = QMessageBox.question(
            self,
            "Confirm Delete",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            failed = []
            for scheme_name in checked_schemes:
                try:
                    self.weight_manager.delete_scheme(self.entity_type, scheme_name)
                except Exception as e:
                    failed.append(f"{scheme_name}: {e}")

            if failed:
                QMessageBox.critical(self, "Error", "Could not delete some schemes:\n" + "\n".join(failed))
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully deleted {len(checked_schemes)} weight scheme(s)." if len(checked_schemes) > 1 else f"Weight scheme '{checked_schemes[0]}' has been deleted."
                )
            self.refresh_schemes_list()

# Quick json fallback support for details loading
import json
