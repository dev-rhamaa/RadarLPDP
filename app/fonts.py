"""Font registry for the Dear PyGui UI: single source of truth for font tags.

Use the FONT_* constants and `bind_last_item_font` instead of raw tag strings so
every font usage can be found with a symbol search.

DPG >= 2.x picks glyph ranges automatically, so a '?' on screen means the font
itself lacks the glyph (see the note next to FONT_PATH_* in config.py).
"""

import os

import dearpygui.dearpygui as dpg

from config import FONT_PATH_MONO, FONT_PATH_UI, FONT_PATH_UI_BOLD

FONT_DEFAULT = "font_default"  # Segoe UI 15, bound globally
FONT_BOLD = "font_bold"        # Segoe UI Bold 16
FONT_MONO = "font_mono"        # Consolas 14, numeric readouts
FONT_DISPLAY = "font_display"  # Segoe UI Bold 30, hero numbers

_REGISTRY_TAG = "font_registry"


def _add_font(path: str, size: int, tag: str) -> bool:
    """Load a TTF into the registry; return False (and log) if the file is missing."""
    if not os.path.exists(path):
        print(f"[fonts] Font not found, skipped '{tag}': {path}")
        return False
    dpg.add_font(path, size, tag=tag)
    return True


def setup_fonts() -> None:
    """Register the system fonts and bind FONT_DEFAULT globally."""
    if dpg.does_item_exist(_REGISTRY_TAG):
        return
    with dpg.font_registry(tag=_REGISTRY_TAG):
        if _add_font(FONT_PATH_UI, 15, FONT_DEFAULT):
            dpg.bind_font(FONT_DEFAULT)
        if _add_font(FONT_PATH_UI_BOLD, 16, FONT_BOLD):
            _add_font(FONT_PATH_UI_BOLD, 30, FONT_DISPLAY)
        _add_font(FONT_PATH_MONO, 14, FONT_MONO)


def bind_last_item_font(font_tag: str) -> None:
    """Bind `font_tag` to the item created last; no-op if that font failed to load."""
    if dpg.does_item_exist(font_tag):
        dpg.bind_item_font(dpg.last_item(), font_tag)
