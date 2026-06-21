"""
main.py — Entry point for the PyQt6 MCDM Decision Support System.

Initialises the QApplication event loop, loads stylesheet, and runs dashboard.
"""

from __future__ import annotations

# stdlib
import sys
from pathlib import Path

# PyQt6
from PyQt6.QtWidgets import QApplication

# ── Ensure workspace root is on sys.path so `app` is an importable package ──
_workspace_root = Path(__file__).resolve().parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

# local gui
from app.gui.app_window import MainWindow
from app.gui.role_window import RoleSelectionWindow
from app.gui.styles import get_stylesheet


class AppController:
    """Manages window transitions between RoleSelectionWindow and MainWindow
    without restarting the application.
    """
    
    def __init__(self):
        self.role_window = None
        self.main_window = None
        self.show_role_selection()
    
    def show_role_selection(self) -> None:
        if self.main_window:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None
        
        self.role_window = RoleSelectionWindow()
        self.role_window.role_selected.connect(self.show_main_window)
        self.role_window.show()
    
    def show_main_window(self, role: str) -> None:
        if self.role_window:
            self.role_window.close()
            self.role_window.deleteLater()
            self.role_window = None
            
        self.main_window = MainWindow(role=role, on_switch_role=self.show_role_selection)
        self.main_window.show()


def main() -> None:
    """Run the PyQt6 MCDM application."""
    app = QApplication(sys.argv)
    
    # Load and apply QSS stylesheet globally
    app.setStyleSheet(get_stylesheet())

    # Create app controller to manage flow
    controller = AppController()

    # Execute app event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
