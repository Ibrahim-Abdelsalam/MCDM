"""
role_window.py — Initial role selection window (Buyer vs Supplier).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.config import COLORS


class RoleCard(QFrame):
    """Clickable card for role selection with hover effects."""

    clicked = pyqtSignal(str)

    def __init__(self, role: str, title: str, subtitle: str, color: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.role = role
        self.base_color = color
        self.hover_color = self._lighten_color(color, 20)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Apply base styling
        self._apply_style(self.base_color)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 20pt; font-weight: bold; color: white; background: transparent;")

        sub_lbl = QLabel(subtitle)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 14pt; color: #f0f4f5; background: transparent;")

        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)

    def _apply_style(self, bg_color: str) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 2px solid transparent;
            }}
        """)

    def _lighten_color(self, hex_color: str, amount: int = 20) -> str:
        """Slightly lighten a hex color for hover effect."""
        hex_color = hex_color.lstrip('#')
        try:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, r + amount)
            g = min(255, g + amount)
            b = min(255, b + amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def enterEvent(self, event) -> None:
        """Hover effect enter."""
        self._apply_style(self.hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Hover effect leave."""
        self._apply_style(self.base_color)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Trigger click signal on release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.role)
        super().mouseReleaseEvent(event)


class RoleSelectionWindow(QMainWindow):
    """Initial window to ask the user 'Who are you?'."""

    role_selected = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Select Your Role")
        self.setFixedSize(500, 380)

        self._setup_ui()

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Who are you?")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 28pt; font-weight: bold; color: #212121;")
        layout.addWidget(header)

        # Subtitle
        subtitle = QLabel("Select your role to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 16pt; color: #7994a0;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Buyer Card
        self.buyer_card = RoleCard(
            role="supplier",  # A Buyer manages Suppliers
            title="BUYER",
            subtitle="I'm sourcing\nsuppliers",
            color=COLORS["buyer_accent"]
        )
        self.buyer_card.clicked.connect(self._on_role_selected)
        cards_layout.addWidget(self.buyer_card)

        # Supplier Card
        self.supplier_card = RoleCard(
            role="buyer",  # A Supplier manages Buyers
            title="SUPPLIER",
            subtitle="I'm offering\nmy products",
            color=COLORS["supplier_accent"]
        )
        self.supplier_card.clicked.connect(self._on_role_selected)
        cards_layout.addWidget(self.supplier_card)

        layout.addLayout(cards_layout)
        layout.addStretch()

    def _on_role_selected(self, role: str) -> None:
        self.role_selected.emit(role)
