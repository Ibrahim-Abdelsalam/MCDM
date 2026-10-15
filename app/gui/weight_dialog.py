"""
weight_dialog.py — Dialog for creating, viewing, and deleting weight schemes using AHP Pairwise Comparison Matrix.
"""

from __future__ import annotations

import json
import numpy as np

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QDoubleSpinBox,
)

from app.core.criteria import CriteriaConfig
from app.core.weight_manager import WeightSchemeManager
from app.config import DIMENSIONS
from app.gui.widgets import confirm_delete, make_scroll_area


class WeightSchemeDialog(QDialog):
    """Dialog to manage criteria weight profiles using AHP Pairwise Comparison."""

    def __init__(self, entity_type: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entity_type = entity_type.lower()
        self.weight_manager = WeightSchemeManager()
        self.criteria_names = CriteriaConfig.get_criteria_names(self.entity_type)

        self.setWindowTitle(f"Manage {entity_type.title()} Weight Schemes (AHP Pairwise)")
        self.setMinimumSize(DIMENSIONS["dialog_width"] + 200, DIMENSIONS["dialog_height"] + 100)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self._setup_ui()
        self.refresh_schemes_list()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QLabel(f"{self.entity_type.title()} Weight Management (AHP Matrix)")
        header.setProperty("role", "header")
        layout.addWidget(header)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self._setup_create_tab()
        self._setup_view_tab()

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(14, 0, 14, 14)
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _setup_create_tab(self) -> None:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)
        tab_layout.setSpacing(14)

        # Left Column: Inputs
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        name_layout = QHBoxLayout()
        name_lbl = QLabel("Scheme Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Quality Focused...")
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.name_input)
        left_layout.addLayout(name_layout)

        # AHP Matrix Table
        n = len(self.criteria_names)
        self.matrix_table = QTableWidget(n, n)
        self.matrix_table.setHorizontalHeaderLabels(self.criteria_names)
        self.matrix_table.setVerticalHeaderLabels(self.criteria_names)
        
        # Populate initial matrix with 1.0s
        self._is_updating = False
        for i in range(n):
            for j in range(n):
                spinbox = QDoubleSpinBox()
                spinbox.setRange(1/9, 9.0)
                spinbox.setDecimals(4)
                spinbox.setValue(1.0)
                if i == j:
                    spinbox.setEnabled(False) # Diagonal is always 1
                
                # We need to capture i and j properly
                spinbox.valueChanged.connect(lambda val, r=i, c=j: self._on_matrix_change(r, c, val))
                self.matrix_table.setCellWidget(i, j, spinbox)

        # Auto resize
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        left_layout.addWidget(self.matrix_table)

        self.save_btn = QPushButton("Calculate & Save Weight Scheme")
        self.save_btn.setProperty("class", "success")
        self.save_btn.style().unpolish(self.save_btn)
        self.save_btn.style().polish(self.save_btn)
        self.save_btn.clicked.connect(self.save_scheme)
        left_layout.addWidget(self.save_btn)

        tab_layout.addWidget(left_pane, 3)

        # Right Column: Normalized Preview
        right_pane = QFrame()
        right_pane.setProperty("role", "card")
        right_pane.style().unpolish(right_pane)
        right_pane.style().polish(right_pane)
        
        right_layout = QVBoxLayout(right_pane)
        
        preview_title = QLabel("Derived Eigenvector Weights")
        preview_title.setProperty("role", "subheader")
        preview_title.style().unpolish(preview_title)
        preview_title.style().polish(preview_title)
        right_layout.addWidget(preview_title)

        self.preview_text = QTextBrowser()
        self.preview_text.setFrameShape(QFrame.Shape.NoFrame)
        right_layout.addWidget(self.preview_text)

        tab_layout.addWidget(right_pane, 1)
        self.tab_widget.addTab(tab, "Create Scheme (AHP)")
        self.update_preview()

    def _on_matrix_change(self, row: int, col: int, val: float) -> None:
        """Handle reciprocal mirroring and update preview."""
        if self._is_updating or row == col:
            return
            
        self._is_updating = True
        try:
            # Set reciprocal
            recip_spinbox = self.matrix_table.cellWidget(col, row)
            if recip_spinbox and val != 0:
                recip_spinbox.setValue(1.0 / val)
        finally:
            self._is_updating = False
            
        self.update_preview()

    def _calculate_eigenvector(self) -> dict[str, float]:
        """Calculate the principal eigenvector of the AHP pairwise matrix."""
        n = len(self.criteria_names)
        if n == 0:
            return {}
            
        matrix = np.ones((n, n))
        for i in range(n):
            for j in range(n):
                widget = self.matrix_table.cellWidget(i, j)
                if isinstance(widget, QDoubleSpinBox):
                    matrix[i, j] = widget.value()
                    
        # Calculate Eigenvalues and Eigenvectors
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        
        # Get the principal eigenvector (corresponding to max eigenvalue)
        max_index = np.argmax(np.real(eigenvalues))
        principal_eigenvector = np.real(eigenvectors[:, max_index])
        
        # Ensure it's positive (sometimes it can be entirely negative)
        if np.sum(principal_eigenvector) < 0:
            principal_eigenvector = -principal_eigenvector
            
        # Normalize
        normalized_weights = principal_eigenvector / np.sum(principal_eigenvector)
        
        return {name: float(weight) for name, weight in zip(self.criteria_names, normalized_weights)}

    def update_preview(self) -> None:
        """Update the derived weights preview."""
        weights = self._calculate_eigenvector()
        if not weights:
            self.preview_text.setHtml("<p>No criteria found.</p>")
            return
            
        html_lines = ["<ul style='line-height: 1.4;'>"]
        for name, w in weights.items():
            html_lines.append(f"<li><b>{name}:</b> {w * 100:.1f}%</li>")
        html_lines.append("</ul>")
        self.preview_text.setHtml("".join(html_lines))

    def save_scheme(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Weight scheme name cannot be empty.")
            return

        weights = self._calculate_eigenvector()
        if not weights:
            return

        try:
            # Save the final computed weights
            self.weight_manager.save_scheme(self.entity_type, name, weights)
            QMessageBox.information(self, "Success", f"Weight scheme '{name}' saved successfully.")
            
            self.name_input.clear()
            # Reset matrix
            self._is_updating = True
            n = len(self.criteria_names)
            for i in range(n):
                for j in range(n):
                    widget = self.matrix_table.cellWidget(i, j)
                    if widget:
                        widget.setValue(1.0)
            self._is_updating = False
            self.update_preview()
            self.refresh_schemes_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save weight scheme: {e}")

    # -------- View Tab --------
    def _setup_view_tab(self) -> None:
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(14, 14, 14, 14)

        list_pane = QWidget()
        list_layout = QVBoxLayout(list_pane)
        self.schemes_list = QListWidget()
        self.schemes_list.currentItemChanged.connect(self.show_scheme_details)
        list_layout.addWidget(self.schemes_list)

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

        details_pane = QFrame()
        details_pane.setProperty("role", "card")
        details_pane.style().unpolish(details_pane)
        details_pane.style().polish(details_pane)
        details_layout = QVBoxLayout(details_pane)
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

    def refresh_schemes_list(self) -> None:
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
            pass

    def show_scheme_details(self) -> None:
        current_item = self.schemes_list.currentItem()
        if not current_item:
            self.details_text.clear()
            return
        scheme_name = current_item.text()
        try:
            norm_weights = self.weight_manager.load_scheme(self.entity_type, scheme_name)
            html_lines = [f"<p><b>Scheme Name:</b> {scheme_name}</p><hr/>"]
            html_lines.append("<table width='100%' cellpadding='3'>")
            html_lines.append("<tr><th>Criterion</th><th align='right'>Ratio</th></tr>")
            for name in self.criteria_names:
                norm_w = norm_weights.get(name, 0.0)
                html_lines.append(f"<tr><td>{name}</td><td align='right'>{norm_w * 100:.1f}%</td></tr>")
            html_lines.append("</table>")
            self.details_text.setHtml("".join(html_lines))
        except Exception as e:
            self.details_text.setPlainText(str(e))

    def delete_selected_scheme(self) -> None:
        checked = [self.schemes_list.item(i).text() for i in range(self.schemes_list.count()) if self.schemes_list.item(i).checkState() == Qt.CheckState.Checked]
        if not checked:
            curr = self.schemes_list.currentItem()
            if curr: checked.append(curr.text())
        if not checked: return

        ans = QMessageBox.question(self, "Confirm Delete", f"Delete {len(checked)} schemes?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            for s in checked:
                try: self.weight_manager.delete_scheme(self.entity_type, s)
                except: pass
            self.refresh_schemes_list()
