"""FFT spectrum display widget.

This module provides the laboratory-grade FFT spectrum analyzer display
for beat frequency estimation and target detection.
"""

import dearpygui.dearpygui as dpg

from config import TARGET_FREQ_THRESHOLD_KHZ, THEME_COLORS
from app.callbacks import (
    set_fft_span,
    zoom_fft_step,
    fit_fft_y,
    reset_fft_view,
    toggle_fft_y_lock,
)


def _create_fft_themes():
    """Create dedicated plot themes for CH1 (Cyan) and CH2 (Amber)."""
    if not dpg.does_item_exist("fft_ch1_theme"):
        with dpg.theme(tag="fft_ch1_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, THEME_COLORS.get("accent", (0, 210, 255, 255)))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.8)

    if not dpg.does_item_exist("fft_ch2_theme"):
        with dpg.theme(tag="fft_ch2_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, THEME_COLORS.get("accent_amber", (255, 184, 0, 255)))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.8)


def create_fft_widget(parent, width, height):
    """Membuat widget UI untuk menampilkan FFT Spectrum dengan toolbar span dan interactive zoom."""
    _create_fft_themes()

    # Sleek compact frequency span toolbar
    with dpg.group(horizontal=True, parent=parent):
        dpg.add_text("SPECTRUM", color=(0, 210, 255))
        if dpg.does_item_exist("font_bold"):
            dpg.bind_item_font(dpg.last_item(), "font_bold")

        dpg.add_spacer(width=4)
        dpg.add_text("Span:", color=(130, 145, 170))
        dpg.add_button(label="10 MHz", small=True, callback=lambda: set_fft_span(10000.0))
        dpg.add_button(label="2 MHz", small=True, callback=lambda: set_fft_span(2000.0))
        dpg.add_button(label="500 kHz", small=True, callback=lambda: set_fft_span(500.0))
        dpg.add_button(label="100 kHz", small=True, callback=lambda: set_fft_span(100.0))

        dpg.add_spacer(width=2)
        dpg.add_button(label="+", small=True, callback=lambda: zoom_fft_step(0.5))
        dpg.add_button(label="-", small=True, callback=lambda: zoom_fft_step(2.0))

        dpg.add_spacer(width=2)
        dpg.add_button(label="dB-Fit", small=True, callback=fit_fft_y)
        dpg.add_button(label="Reset", small=True, callback=reset_fft_view)

        dpg.add_spacer(width=4)
        dpg.add_checkbox(label="dB-Lock", default_value=True, callback=toggle_fft_y_lock, tag="fft_lock_checkbox")

    with dpg.plot(
        label="Beat Frequency Spectrum (FFT)",
        parent=parent,
        height=-1,
        width=-1,
        tag="fft_plot"
    ):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        
        x_axis = dpg.add_plot_axis(
            dpg.mvXAxis,
            label="Beat Frequency (kHz)",
            tag="fft_xaxis"
        )

        y_axis = dpg.add_plot_axis(
            dpg.mvYAxis,
            label="Magnitude (dB)",
            tag="fft_yaxis",
            lock_min=True,
            lock_max=True
        )

        ch1_series = dpg.add_line_series(
            [],
            [],
            label="CH0 (Beat RF)",
            parent="fft_yaxis",
            tag="fft_ch1_series"
        )
        dpg.bind_item_theme(ch1_series, "fft_ch1_theme")

        ch2_series = dpg.add_line_series(
            [],
            [],
            label="CH2 (Sync)",
            parent="fft_yaxis",
            tag="fft_ch2_series"
        )
        dpg.bind_item_theme(ch2_series, "fft_ch2_theme")