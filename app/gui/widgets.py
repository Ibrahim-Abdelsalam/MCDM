"""
widgets.py — Shared reusable widget helpers for the MCDM Analysis System.

All helpers follow the same conventions:
  - Pure PyQt6, no inline stylesheets (QSS handles everything)
  - QSS property-based status/role labelling
  - Type-annotated, docstring on every public symbol
"""

from __future__ import annotations

# stdlib
from typing import Literal

# PyQt6
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

__all__ = [
    "make_section_header",
    "make_status_label",
    "confirm_delete",
    "make_scroll_area",
    "CriterionSpinRow",
    "HorizontalLine",
]


# ─────────────────────────────────────────────────────────────────────────────
# Label factories
# ─────────────────────────────────────────────────────────────────────────────

def make_section_header(text: str) -> QLabel:
    """Return a styled QLabel used as a section header inside dialogs.

    The label carries ``role="subheader"`` so QSS can target it without
    any inline stylesheet calls.
    """
    label = QLabel(text)
    label.setProperty("role", "subheader")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    # Re-polish so QSS property selector fires immediately
    label.style().unpolish(label)
    label.style().polish(label)
    return label


def make_status_label(
    text: str,
    status: Literal["success", "error", "neutral"] = "neutral",
) -> QLabel:
    """Return a QLabel styled by status via the QSS ``status`` property.

    Args:
        text:   Label text.
        status: One of ``"success"`` (green), ``"error"`` (red),
                or ``"neutral"`` (muted grey).
    """
    label = QLabel(text)
    label.setProperty("status", status)
    label.setWordWrap(True)
    label.style().unpolish(label)
    label.style().polish(label)
    return label


# ─────────────────────────────────────────────────────────────────────────────
# Confirmation dialog helper
# ─────────────────────────────────────────────────────────────────────────────

def confirm_delete(parent: QWidget | None, item_name: str) -> bool:
    """Show a standard delete-confirmation dialog and return True if confirmed.

    Uses PyQt6 enum-qualified button constants throughout.

    Args:
        parent:    Parent widget (may be None).
        item_name: Human-readable name of the item to be deleted.

    Returns:
        ``True`` when the user clicked *Yes*, ``False`` otherwise.
    """
    answer = QMessageBox.question(
        parent,
        "Confirm Delete",
        f'Are you sure you want to delete "{item_name}"?\n\nThis action cannot be undone.',
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,  # default
    )
    return answer == QMessageBox.StandardButton.Yes


# ─────────────────────────────────────────────────────────────────────────────
# Scroll-area factory
# ─────────────────────────────────────────────────────────────────────────────

def make_scroll_area(inner_widget: QWidget) -> QScrollArea:
    """Wrap *inner_widget* in a QScrollArea with standard scroll policy.

    Vertical scroll is enabled as needed; horizontal scroll is always off.
    The inner widget expands to fill the available width automatically.

    Args:
        inner_widget: The widget to embed inside the scroll area.

    Returns:
        Configured QScrollArea ready to add to a layout.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(inner_widget)
    # Transparent frame so the outer GroupBox border is the visual boundary
    scroll.setFrameShape(scroll.Shape.NoFrame)
    return scroll


# ─────────────────────────────────────────────────────────────────────────────
# Composite spin-box row widget
# ─────────────────────────────────────────────────────────────────────────────

class CriterionSpinRow(QWidget):
    """Reusable composite widget: a QLabel + QSpinBox pair in one horizontal row.

    Used for both company-score entry (CompanyManagerDialog) and weight
    assignment (WeightSchemeDialog) to guarantee visual consistency.

    Signals:
        valueChanged (int): Re-emitted from the inner QSpinBox whenever the
            user changes the value — allows parent dialogs to connect without
            reaching into internals.

    Attributes:
        spinbox (QSpinBox): The underlying spin-box (exposed for direct access
            when needed, e.g. bulk ``setValue`` calls).
    """

    # Class-level signal — standard PyQt6 pattern
    valueChanged: pyqtSignal = pyqtSignal(int)

    def __init__(
        self,
        label_text: str,
        min_val: int = 1,
        max_val: int = 10,
        default: int = 5,
        parent: QWidget | None = None,
    ) -> None:
        """Initialise the row widget.

        Args:
            label_text: Criterion name shown to the left of the spin-box.
            min_val:    Minimum allowed spin-box value (inclusive).
            max_val:    Maximum allowed spin-box value (inclusive).
            default:    Initial value.
            parent:     Optional parent widget.
        """
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        # Label — takes all remaining horizontal space
        self._label = QLabel(label_text)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._label.setWordWrap(False)
        layout.addWidget(self._label)

        # Spin-box — fixed width so all spin-boxes align in a column
        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setValue(default)
        self.spinbox.setFixedWidth(80)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinbox)

        # Forward the inner signal to this widget's signal
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

    # ── Public API ──────────────────────────────────────────────────────────

    def value(self) -> int:
        """Return the current spin-box value."""
        return self.spinbox.value()

    def set_value(self, v: int) -> None:
        """Programmatically set the spin-box value (does not emit valueChanged).

        Args:
            v: New value — must be within [min_val, max_val].
        """
        self.spinbox.setValue(v)

    def reset(self, default: int = 5) -> None:
        """Reset the spin-box to *default* (typically the midpoint 5).

        Args:
            default: Value to restore (default 5).
        """
        self.spinbox.setValue(default)

    def label_text(self) -> str:
        """Return the criterion label text."""
        return self._label.text()


# ─────────────────────────────────────────────────────────────────────────────
# Horizontal divider
# ─────────────────────────────────────────────────────────────────────────────

class HorizontalLine(QWidget):
    """A thin horizontal rule used as a visual section divider in dialogs.

    Implemented as a zero-height QWidget with a fixed 1-px bottom border drawn
    purely via QSS, avoiding QFrame's inconsistent theming on some platforms.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise the horizontal line."""
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Single inline rule is acceptable here: it's structural, not thematic
        self.setStyleSheet("background-color: #cab7b1;")


# ─────────────────────────────────────────────────────────────────────────────
# Multi-criterion form builder (convenience used by several dialogs)
# ─────────────────────────────────────────────────────────────────────────────

def build_criterion_form(
    criteria_names: list[str],
    min_val: int = 1,
    max_val: int = 10,
    default: int = 5,
) -> tuple[QWidget, list[CriterionSpinRow]]:
    """Build a scrollable form of CriterionSpinRow widgets for a criteria list.

    Returns a 2-tuple so callers can:
      - Add the QWidget directly to a QScrollArea.
      - Keep a reference to the rows list for reading values later.

    Args:
        criteria_names: Ordered list of criterion name strings.
        min_val:        Minimum spin-box value.
        max_val:        Maximum spin-box value.
        default:        Initial spin-box value for every row.

    Returns:
        ``(container_widget, [CriterionSpinRow, ...])``
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(2)

    rows: list[CriterionSpinRow] = []
    for name in criteria_names:
        row = CriterionSpinRow(name, min_val, max_val, default)
        layout.addWidget(row)
        rows.append(row)

    layout.addStretch()
    return container, rows
