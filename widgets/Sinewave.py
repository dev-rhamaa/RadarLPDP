"""Sinewave oscilloscope widget.

This module provides the dual-channel time-domain waveform oscilloscope display.
"""

import dearpygui.dearpygui as dpg

from config import THEME_COLORS


def _create_scope_themes():
    """Create dedicated plot themes for dual-beam oscilloscope."""
    if not dpg.does_item_exist("scope_ch1_theme"):
        with dpg.theme(tag="scope_ch1_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, THEME_COLORS.get("accent", (0, 210, 255, 230)))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.6)

    if not dpg.does_item_exist("scope_ch2_theme"):
        with dpg.theme(tag="scope_ch2_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, THEME_COLORS.get("accent_amber", (255, 184, 0, 230)))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.6)


def create_sinewave_widget(parent, width, height):
    """Membuat widget UI untuk menampilkan waveform mentah."""
    _create_scope_themes()

    with dpg.plot(
        label="Raw Time-Domain Waveforms (CH0 & CH2)",
        parent=parent,
        height=-1,
        width=-1,
        tag="sinewave_plot"
    ):
            dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
            
            x_axis = dpg.add_plot_axis(
                dpg.mvXAxis,
                label="Time (µs)",
                tag="sinewave_xaxis"
            )
            y_axis = dpg.add_plot_axis(
                dpg.mvYAxis,
                label="ADC Amplitude",
                tag="sinewave_yaxis"
            )

            ch1_series = dpg.add_line_series(
                [],
                [],
                label="CH0 (Raw)",
                parent="sinewave_yaxis",
                tag="sinewave_ch1_series"
            )
            dpg.bind_item_theme(ch1_series, "scope_ch1_theme")

            ch2_series = dpg.add_line_series(
                [],
                [],
                label="CH2 (Sync)",
                parent="sinewave_yaxis",
                tag="sinewave_ch2_series"
            )
            dpg.bind_item_theme(ch2_series, "scope_ch2_theme")