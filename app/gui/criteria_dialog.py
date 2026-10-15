"""
criteria_dialog.py — Dialog for managing dynamic evaluation criteria.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.criteria import CriteriaConfig
from app.config import DIMENSIONS


class CriteriaManagerDialog(QDialog):
    """Standalone dialog to manage evaluation criteria for a specific role."""

    def __init__(self, entity_type: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entity_type = entity_type.lower()
        self.setWindowTitle(f"Manage {self.entity_type.title()} Evaluation Criteria")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header = QLabel(f"{self.entity_type.title()} Criteria Definitions")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)

        # Main horizontal layout: List on left, form on right
        h_layout = QHBoxLayout()
        h_layout.setSpacing(14)

        # Left: List Widget
        self.criteria_list = QListWidget()
        self.criteria_list.currentItemChanged.connect(self._on_item_selected)
        h_layout.addWidget(self.criteria_list, 2)

        # Right: Form and Actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["benefit", "cost"])
        
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Type:", self.type_combo)
        
        right_layout.addLayout(form_layout)

        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self._add_criterion)
        
        self.update_btn = QPushButton("Update Selected")
        self.update_btn.clicked.connect(self._update_criterion)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._remove_criterion)

        right_layout.addWidget(self.add_btn)
        right_layout.addWidget(self.update_btn)
        right_layout.addWidget(self.remove_btn)
        right_layout.addStretch()

        h_layout.addWidget(right_panel, 3)
        layout.addLayout(h_layout)

        # Bottom: Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def refresh_list(self) -> None:
        self.criteria_list.clear()
        criteria_dict = CriteriaConfig.get_all_criteria(self.entity_type)
        for name, info in criteria_dict.items():
            self.criteria_list.addItem(f"{name} ({info.get('type', 'benefit')})")
        
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)

    def _on_item_selected(self) -> None:
        item = self.criteria_list.currentItem()
        if not item:
            return
            
        text = item.text()
        # Format is "Name (type)"
        name_part = text.rsplit(" (", 1)[0]
        
        criteria_dict = CriteriaConfig.get_all_criteria(self.entity_type)
        if name_part in criteria_dict:
            self.name_input.setText(name_part)
            c_type = criteria_dict[name_part].get("type", "benefit")
            idx = self.type_combo.findText(c_type)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

    def _add_criterion(self) -> None:
        name = self.name_input.text().strip()
        c_type = self.type_combo.currentText()
        if not name:
            QMessageBox.warning(self, "Error", "Criterion name cannot be empty.")
            return
            
        try:
            CriteriaConfig.add_criterion(self.entity_type, name, c_type)
            self.refresh_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _update_criterion(self) -> None:
        item = self.criteria_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "No criterion selected.")
            return
            
        old_name = item.text().rsplit(" (", 1)[0]
        new_name = self.name_input.text().strip()
        c_type = self.type_combo.currentText()
        
        if not new_name:
            QMessageBox.warning(self, "Error", "Criterion name cannot be empty.")
            return
            
        try:
            CriteriaConfig.update_criterion(self.entity_type, old_name, new_name, c_type)
            self.refresh_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _remove_criterion(self) -> None:
        item = self.criteria_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "No criterion selected.")
            return
            
        name = item.text().rsplit(" (", 1)[0]
        
        # Prevent removing all criteria
        if self.criteria_list.count() <= 1:
            QMessageBox.warning(self, "Error", "Cannot remove the last criterion.")
            return
            
        ans = QMessageBox.question(
            self, "Confirm Remove", f"Remove criterion '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            try:
                CriteriaConfig.delete_criterion(self.entity_type, name)
                self.refresh_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
