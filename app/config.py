"""Shared configuration for the MCDM DSS application."""

from __future__ import annotations

from pathlib import Path


# ── Core constants (DO NOT REMOVE) ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_VIKOR_V = 0.5
SCORE_MIN = 1
SCORE_MAX = 10


# ── PyQt6 UI design tokens ──────────────────────────────────────────────────
# Palette derived from: #005a6d · #7994a0 · #8c8c8c · #39466c
#                       #675584 · #cab7b1 · #0f4662
COLORS: dict[str, str] = {
    # Brand
    "primary":         "#0f4662",   # deep navy
    "primary_dark":    "#0a2e40",   # darker navy
    "secondary":       "#39466c",   # slate blue
    "accent":          "#675584",   # muted violet
    # Semantic
    "success":         "#2e7d5e",   # tonal teal-green
    "warning":         "#9a7c52",   # tonal warm amber
    "danger":          "#8c3d3d",   # tonal muted crimson
    # Backgrounds
    "bg_main":         "#f0f4f5",   # near-white teal tint
    "bg_panel":        "#ffffff",
    "bg_header":       "#0f4662",
    # Text
    "text_light":      "#ffffff",
    "text_dark":       "#212121",
    "text_muted":      "#7994a0",   # muted blue-grey
    # Borders & highlights
    "border":          "#cab7b1",   # warm blush
    "highlight":       "#ddeaed",   # pale teal tint
    # Entity accents
    "buyer_accent":    "#39466c",   # slate blue
    "supplier_accent": "#0f4662",   # deep navy
}

FONTS: dict[str, object] = {
    "header_family":   "Segoe UI",
    "header_size":     24,
    "subheader_size":  18,
    "body_size":       14,
    "small_size":      12,
}

DIMENSIONS: dict[str, int] = {
    "main_width":    1200,
    "main_height":   800,
    "dialog_width":  1000,
    "dialog_height": 700,
    "panel_width":   400,
    "btn_height":    40,
    "pad":           16,
}
