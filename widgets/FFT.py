"""FFT spectrum display widget.

This module provides the laboratory-grade FFT spectrum analyzer display
for beat frequency estimation and target detection.
"""

import dearpygui.dearpygui as dpg

from config import TARGET_FREQ_THRESHOLD_KHZ, THEME_COLORS


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
    """Membuat widget UI untuk menampilkan FFT Spectrum."""
    _create_fft_themes()

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
            dpg.set_axis_limits("fft_xaxis", 0, TARGET_FREQ_THRESHOLD_KHZ)

            y_axis = dpg.add_plot_axis(
                dpg.mvYAxis,
                label="Magnitude (dB)",
                tag="fft_yaxis"
            )
            dpg.set_axis_limits("fft_yaxis", -110.0, 10.0)

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