"""Time-domain oscilloscope widget (display-only card).

Time/Div, V/Div, fit and lock controls live in the menu bar "Scope" menu.
"""

import dearpygui.dearpygui as dpg

from config import THEME_COLORS
from widgets.common import card_header, line_theme


def create_sinewave_widget(parent, width, height):
    """Oscilloscope card: header with current Time/Div · V/Div + raw waveform plot."""
    line_theme("scope_ch1_theme", THEME_COLORS["accent"], 1.4)
    line_theme("scope_ch2_theme", THEME_COLORS["accent_amber"], 1.4)

    card_header(parent, "Oscilloscope", "Raw CH0 / CH2",
                readout_tag="scope_div_readout", readout_default="")

    with dpg.plot(parent=parent, height=-1, width=-1, no_title=True, no_menus=True,
                  no_mouse_pos=True, tag="sinewave_plot"):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast, horizontal=True)

        dpg.add_plot_axis(dpg.mvXAxis, label="µs", tag="sinewave_xaxis")
        dpg.add_plot_axis(dpg.mvYAxis, label="ADC counts", tag="sinewave_yaxis",
                          lock_min=True, lock_max=True)

        ch1 = dpg.add_line_series([], [], label="CH0", parent="sinewave_yaxis", tag="sinewave_ch1_series")
        dpg.bind_item_theme(ch1, "scope_ch1_theme")
        ch2 = dpg.add_line_series([], [], label="CH2", parent="sinewave_yaxis", tag="sinewave_ch2_series")
        dpg.bind_item_theme(ch2, "scope_ch2_theme")
