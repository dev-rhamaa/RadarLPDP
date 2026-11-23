"""FFT spectrum display widget (display-only card).

Span, zoom, fit and lock controls live in the menu bar "Spectrum" menu.
"""

import dearpygui.dearpygui as dpg

from config import THEME_COLORS
from widgets.common import card_header, line_theme


def create_fft_widget(parent, width, height):
    """Spectrum card: header with live cursor read-out + beat-frequency plot."""
    line_theme("fft_ch1_theme", THEME_COLORS["accent"], 1.6)
    line_theme("fft_ch2_theme", THEME_COLORS["accent_amber"], 1.4)

    card_header(parent, "Spectrum", "Beat frequency  ·  1 kHz = 3 m",
                readout_tag="fft_cursor_readout", readout_default="hover plot for range")

    with dpg.plot(parent=parent, height=-1, width=-1, no_title=True, no_menus=True,
                  no_mouse_pos=True, crosshairs=True, tag="fft_plot"):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast, horizontal=True)

        dpg.add_plot_axis(dpg.mvXAxis, label="kHz", tag="fft_xaxis")
        dpg.add_plot_axis(dpg.mvYAxis, label="dBm", tag="fft_yaxis", lock_min=True, lock_max=True)

        ch1 = dpg.add_line_series([], [], label="CH0", parent="fft_yaxis", tag="fft_ch1_series")
        dpg.bind_item_theme(ch1, "fft_ch1_theme")
        ch2 = dpg.add_line_series([], [], label="CH2", parent="fft_yaxis", tag="fft_ch2_series")
        dpg.bind_item_theme(ch2, "fft_ch2_theme")
