"""Target & telemetry card: one hero read-out (CH0 target range) plus two compact tables."""

import dearpygui.dearpygui as dpg

from app.fonts import FONT_DISPLAY, FONT_MONO, bind_last_item_font
from config import FMCW_BEAT_MAX_KHZ, FMCW_BEAT_MIN_KHZ, RADAR_MAX_RANGE, THEME_COLORS
from widgets.common import card_header

_CHANNELS = (("ch1", "CH0", "accent"), ("ch2", "CH2", "accent_amber"))


def _section_label(text: str) -> None:
    dpg.add_text(text.upper(), color=THEME_COLORS["text_faint"])


def _value_cell(tag: str) -> None:
    dpg.add_text("—", tag=tag)
    bind_last_item_font(FONT_MONO)


def create_metrics_widget(parent: int | str, width: int, height: int) -> None:
    card_header(parent, "Targets", f"{FMCW_BEAT_MIN_KHZ:.0f} kHz - {FMCW_BEAT_MAX_KHZ / 1000:.0f} MHz"
                f"  ·  max {RADAR_MAX_RANGE:.0f} km")

    with dpg.group(parent=parent):
        dpg.add_spacer(height=2)
        # Hero read-out: nearest CH0 target range
        with dpg.group(horizontal=True, horizontal_spacing=6):
            dpg.add_text("—", tag="metric_range_big", color=THEME_COLORS["accent"])
            bind_last_item_font(FONT_DISPLAY)
            with dpg.group():
                dpg.add_spacer(height=8)
                dpg.add_text("km  ·  CH0 target range", color=THEME_COLORS["text_muted"])

        dpg.add_spacer(height=6)
        _section_label("Detection")
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=False,
                       borders_innerV=False, borders_outerV=False,
                       policy=dpg.mvTable_SizingStretchSame):
            for label in ("Ch", "Beat kHz", "Range km", "Power dBm"):
                dpg.add_table_column(label=label)
            for prefix, name, color_key in _CHANNELS:
                with dpg.table_row():
                    dpg.add_text(name, color=THEME_COLORS[color_key])
                    _value_cell(f"{prefix}_target_freq")
                    _value_cell(f"{prefix}_target_range")
                    _value_cell(f"{prefix}_target_mag")

        dpg.add_spacer(height=6)
        _section_label("Spectrum peak")
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=False,
                       borders_innerV=False, borders_outerV=False,
                       policy=dpg.mvTable_SizingStretchSame):
            for label in ("Ch", "Peak kHz", "Peak dBm"):
                dpg.add_table_column(label=label)
            for prefix, name, color_key in _CHANNELS:
                with dpg.table_row():
                    dpg.add_text(name, color=THEME_COLORS[color_key])
                    _value_cell(f"{prefix}_peak_freq")
                    _value_cell(f"{prefix}_peak_mag")
