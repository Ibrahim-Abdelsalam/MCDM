"""
styles.py — centralised QSS stylesheet for the MCDM Analysis System.

All colours are pulled from config.COLORS so that changing the palette in one
place propagates through the entire application automatically.

Usage
-----
    from gui.styles import get_stylesheet
    app.setStyleSheet(get_stylesheet())
"""

from __future__ import annotations

# stdlib — none needed here
# PyQt6 — none needed here (pure string builder)
# local
from app.config import COLORS, FONTS, DIMENSIONS

__all__ = ["get_stylesheet"]


def get_stylesheet() -> str:
    """Return the full QSS stylesheet string for the application.

    Builds QSS by interpolating values from COLORS, FONTS, and DIMENSIONS so
    that a single palette change in config.py updates every widget instantly.
    """
    C = COLORS
    F = FONTS
    D = DIMENSIONS

    return f"""
/* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL / APPLICATION
   ═══════════════════════════════════════════════════════════════════════════ */

QMainWindow,
QDialog {{
    background-color: {C["bg_main"]};
    font-family: "{F["header_family"]}", "Helvetica Neue", Arial, sans-serif;
    font-size: {F["body_size"]}pt;
    color: {C["text_dark"]};
}}

QWidget {{
    background-color: transparent;
    color: {C["text_dark"]};
    font-family: "{F["header_family"]}", "Helvetica Neue", Arial, sans-serif;
    font-size: {F["body_size"]}pt;
}}

/* Toplevel containers painted explicitly */
QMainWindow > QWidget,
QDialog > QWidget {{
    background-color: {C["bg_main"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   LABELS
   ═══════════════════════════════════════════════════════════════════════════ */

QLabel {{
    background-color: transparent;
    color: {C["text_dark"]};
}}

QLabel[role="header"] {{
    background-color: {C["bg_header"]};
    color: {C["text_light"]};
    font-size: {F["header_size"]}pt;
    font-weight: 700;
    padding: 14px {D["pad"]}px;
    border-radius: 0px;
}}

QLabel[role="subheader"] {{
    color: {C["primary"]};
    font-size: {F["subheader_size"]}pt;
    font-weight: 600;
}}

QLabel[role="muted"] {{
    color: {C["text_muted"]};
    font-size: {F["small_size"]}pt;
}}

QLabel[status="success"] {{
    color: {C["success"]};
    font-weight: 600;
}}

QLabel[status="error"] {{
    color: {C["danger"]};
    font-weight: 600;
}}

QLabel[status="neutral"] {{
    color: {C["text_muted"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   BUTTONS  (default, hover, pressed + class variants)
   ═══════════════════════════════════════════════════════════════════════════ */

QPushButton {{
    background-color: {C["primary"]};
    color: {C["text_light"]};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: {F["body_size"]}pt;
    font-weight: 600;
    min-height: {D["btn_height"]}px;
    outline: none;
}}

QPushButton:hover {{
    background-color: {C["primary_dark"]};
}}

QPushButton:pressed {{
    background-color: {C["secondary"]};
    padding-top: 10px;
    padding-bottom: 6px;
}}

QPushButton:disabled {{
    background-color: {C["border"]};
    color: {C["text_muted"]};
}}

/* ── Success variant ── */
QPushButton[class="success"] {{
    background-color: {C["success"]};
}}
QPushButton[class="success"]:hover {{
    background-color: #236148;
}}
QPushButton[class="success"]:pressed {{
    background-color: #1a4a37;
}}

/* ── Danger / destructive variant ── */
QPushButton[class="danger"] {{
    background-color: {C["danger"]};
}}
QPushButton[class="danger"]:hover {{
    background-color: #6e2e2e;
}}
QPushButton[class="danger"]:pressed {{
    background-color: #4f2020;
}}

/* ── Secondary / muted variant ── */
QPushButton[class="secondary"] {{
    background-color: {C["secondary"]};
    color: {C["text_light"]};
}}
QPushButton[class="secondary"]:hover {{
    background-color: #2d3757;
}}
QPushButton[class="secondary"]:pressed {{
    background-color: #212840;
}}

/* ── Accent variant ── */
QPushButton[class="accent"] {{
    background-color: {C["accent"]};
}}
QPushButton[class="accent"]:hover {{
    background-color: #513f68;
}}

/* ── Flat / text-only variant ── */
QPushButton[class="flat"] {{
    background-color: transparent;
    color: {C["primary"]};
    border: 1px solid {C["primary"]};
}}
QPushButton[class="flat"]:hover {{
    background-color: {C["highlight"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   INPUT WIDGETS
   ═══════════════════════════════════════════════════════════════════════════ */

QLineEdit,
QTextEdit,
QPlainTextEdit {{
    background-color: {C["bg_panel"]};
    border: 1px solid {C["border"]};
    border-radius: 5px;
    padding: 6px 10px;
    color: {C["text_dark"]};
    selection-background-color: {C["primary"]};
    selection-color: {C["text_light"]};
}}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {{
    border: 2px solid {C["primary"]};
    padding: 5px 9px;
}}

QLineEdit:disabled,
QTextEdit:disabled {{
    background-color: {C["bg_main"]};
    color: {C["text_muted"]};
}}

QSpinBox,
QDoubleSpinBox {{
    background-color: {C["bg_panel"]};
    border: 1px solid {C["border"]};
    border-radius: 5px;
    padding: 4px 8px;
    min-width: 70px;
    color: {C["text_dark"]};
}}

QSpinBox:focus,
QDoubleSpinBox:focus {{
    border: 2px solid {C["primary"]};
}}

QSpinBox::up-button,
QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    border-left: 1px solid {C["border"]};
    border-bottom: 1px solid {C["border"]};
    border-top-right-radius: 4px;
    background: {C["bg_main"]};
    width: 20px;
}}

QSpinBox::down-button,
QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    border-left: 1px solid {C["border"]};
    border-top: 1px solid {C["border"]};
    border-bottom-right-radius: 4px;
    background: {C["bg_main"]};
    width: 20px;
}}

QSpinBox::up-button:hover,
QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover,
QDoubleSpinBox::down-button:hover {{
    background: {C["highlight"]};
}}

QComboBox {{
    background-color: {C["bg_panel"]};
    border: 1px solid {C["border"]};
    border-radius: 5px;
    padding: 5px 10px;
    min-width: 120px;
    color: {C["text_dark"]};
}}

QComboBox:focus {{
    border: 2px solid {C["primary"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {C["bg_panel"]};
    border: 1px solid {C["border"]};
    selection-background-color: {C["primary"]};
    selection-color: {C["text_light"]};
    outline: none;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   CHECKBOXES & RADIO BUTTONS
   ═══════════════════════════════════════════════════════════════════════════ */

QCheckBox,
QRadioButton {{
    spacing: 8px;
    color: {C["text_dark"]};
    background-color: transparent;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {C["border"]};
    background-color: {C["bg_panel"]};
}}

QCheckBox::indicator:checked {{
    background-color: {C["primary"]};
    border-color: {C["primary"]};
    image: none;
}}

QCheckBox::indicator:hover {{
    border-color: {C["primary"]};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid {C["border"]};
    background-color: {C["bg_panel"]};
}}

QRadioButton::indicator:checked {{
    background-color: {C["primary"]};
    border-color: {C["primary"]};
}}

QRadioButton::indicator:hover {{
    border-color: {C["primary"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   SLIDER (VIKOR v parameter)
   ═══════════════════════════════════════════════════════════════════════════ */

QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {C["border"]};
    border-radius: 3px;
    margin: 0 4px;
}}

QSlider::handle:horizontal {{
    background: {C["primary"]};
    border: 2px solid {C["primary_dark"]};
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -6px -1px;
}}

QSlider::handle:horizontal:hover {{
    background: {C["primary_dark"]};
    border-color: {C["secondary"]};
}}

QSlider::sub-page:horizontal {{
    background: {C["primary"]};
    border-radius: 3px;
    height: 6px;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   PROGRESS BAR
   ═══════════════════════════════════════════════════════════════════════════ */

QProgressBar {{
    border: 1px solid {C["border"]};
    border-radius: 5px;
    background-color: {C["bg_main"]};
    text-align: center;
    color: {C["text_dark"]};
    font-size: {F["small_size"]}pt;
    min-height: 18px;
}}

QProgressBar::chunk {{
    background-color: {C["primary"]};
    border-radius: 4px;
    margin: 1px;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   GROUP BOX
   ═══════════════════════════════════════════════════════════════════════════ */

QGroupBox {{
    font-size: {F["subheader_size"]}pt;
    font-weight: 700;
    color: {C["primary_dark"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    background-color: {C["bg_panel"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    top: -1px;
    background-color: {C["bg_panel"]};
    color: {C["primary"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   TABLE WIDGET
   ═══════════════════════════════════════════════════════════════════════════ */

QTableWidget {{
    background-color: {C["bg_panel"]};
    alternate-background-color: {C["highlight"]};
    gridline-color: {C["border"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
    selection-background-color: {C["primary"]};
    selection-color: {C["text_light"]};
    font-size: {F["body_size"]}pt;
}}

QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {C["primary"]};
    color: {C["text_light"]};
}}

QHeaderView::section {{
    background-color: {C["primary"]};
    color: {C["text_light"]};
    font-weight: 700;
    font-size: {F["body_size"]}pt;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {C["primary_dark"]};
    border-bottom: 1px solid {C["primary_dark"]};
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {C["primary_dark"]};
}}

QTableCornerButton::section {{
    background-color: {C["primary"]};
    border: none;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   LIST WIDGET
   ═══════════════════════════════════════════════════════════════════════════ */

QListWidget {{
    background-color: {C["bg_panel"]};
    border: 1px solid {C["border"]};
    border-radius: 6px;
    alternate-background-color: {C["highlight"]};
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {C["highlight"]};
    color: {C["text_dark"]};
}}

QListWidget::item:selected {{
    background-color: {C["primary"]};
    color: {C["text_light"]};
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {C["highlight"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   TAB WIDGET
   ═══════════════════════════════════════════════════════════════════════════ */

QTabWidget::pane {{
    border: 1px solid {C["border"]};
    border-top: none;
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: {C["bg_panel"]};
    padding: 12px;
}}

QTabBar::tab {{
    background-color: {C["bg_main"]};
    color: {C["text_muted"]};
    border: 1px solid {C["border"]};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 22px;
    margin-right: 3px;
    font-size: {F["body_size"]}pt;
    font-weight: 500;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    background-color: {C["bg_panel"]};
    color: {C["primary"]};
    font-weight: 700;
    border-bottom: 2px solid {C["primary"]};
    margin-bottom: -1px;
}}

QTabBar::tab:hover:!selected {{
    background-color: {C["highlight"]};
    color: {C["primary_dark"]};
}}


/* ═══════════════════════════════════════════════════════════════════════════
   SCROLL AREA / SCROLL BARS
   ═══════════════════════════════════════════════════════════════════════════ */

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background: {C["bg_main"]};
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {C["border"]};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {C["text_muted"]};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background: {C["bg_main"]};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {C["border"]};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {C["text_muted"]};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   TOOLTIPS
   ═══════════════════════════════════════════════════════════════════════════ */

QToolTip {{
    background-color: {C["primary_dark"]};
    color: {C["text_light"]};
    border: 1px solid {C["primary"]};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: {F["small_size"]}pt;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   MESSAGE BOX
   ═══════════════════════════════════════════════════════════════════════════ */

QMessageBox {{
    background-color: {C["bg_panel"]};
}}

QMessageBox QLabel {{
    color: {C["text_dark"]};
    font-size: {F["body_size"]}pt;
    min-width: 260px;
}}

QMessageBox QPushButton {{
    min-width: 80px;
}}


/* ═══════════════════════════════════════════════════════════════════════════
   FRAME  (used as divider / card containers)
   ═══════════════════════════════════════════════════════════════════════════ */

QFrame[frameShape="4"],   /* HLine */
QFrame[frameShape="5"] {{ /* VLine */
    color: {C["border"]};
    background-color: {C["border"]};
    border: none;
    max-height: 1px;
}}

QFrame[role="card"] {{
    background-color: {C["bg_panel"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    padding: 10px;
}}
"""
