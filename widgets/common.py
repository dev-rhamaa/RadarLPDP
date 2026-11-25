"""Shared building blocks for dashboard cards.

Panels are display-only: a card has a title on the left and an optional live
read-out on the right. Settings live in the menu bar / Settings dialog.
"""

from typing import Optional

import dearpygui.dearpygui as dpg

from app.fonts import FONT_BOLD, FONT_MONO, bind_last_item_font
from config import THEME_COLORS


def card_header(parent, title: str, subtitle: str = "", readout_tag: Optional[str] = None,
                readout_default: str = "") -> None:
    """Card title row: bold title + muted subtitle, with an optional right-aligned mono read-out.

    The read-out sits in a 2-column stretch table so it stays right-aligned at any width.
    """
    if not dpg.does_item_exist("card_header_theme"):
        with dpg.theme(tag="card_header_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 0, 0)

    with dpg.table(parent=parent, header_row=False, borders_innerH=False, borders_outerH=False,
                   borders_innerV=False, borders_outerV=False, pad_outerX=False,
                   policy=dpg.mvTable_SizingStretchProp) as header:
        dpg.bind_item_theme(header, "card_header_theme")
        dpg.add_table_column(init_width_or_weight=1.0)
        if readout_tag:
            dpg.add_table_column(init_width_or_weight=0.0, width_fixed=True)
        with dpg.table_row():
            with dpg.group(horizontal=True, horizontal_spacing=8):
                dpg.add_text(title, color=THEME_COLORS["text"])
                bind_last_item_font(FONT_BOLD)
                if subtitle:
                    dpg.add_text(subtitle, color=THEME_COLORS["text_muted"])
            if readout_tag:
                dpg.add_text(readout_default, tag=readout_tag, color=THEME_COLORS["text_muted"])
                bind_last_item_font(FONT_MONO)


def line_theme(tag: str, color, weight: float = 1.6) -> str:
    """Create (once) a line-series theme with the given color and weight; return its tag."""
    if not dpg.does_item_exist(tag):
        with dpg.theme(tag=tag):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, weight, category=dpg.mvThemeCat_Plots)
    return tag
