"""Sinewave oscilloscope widget.

This module provides the dual-channel time-domain waveform oscilloscope display
with dedicated Time/Div and V/Div rotary controls.
"""

import dearpygui.dearpygui as dpg

from config import THEME_COLORS
from app.callbacks import (
    set_scope_timebase,
    zoom_scope_step,
    fit_scope_y,
    reset_scope_view,
    toggle_scope_y_lock,
    TIME_DIV_OPTIONS,
    V_DIV_OPTIONS,
    set_scope_time_div,
    set_scope_v_div,
    step_scope_time_div,
    step_scope_v_div,
)


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
    """Membuat widget UI untuk menampilkan waveform mentah dengan toolbar Time/Div dan V/Div."""
    _create_scope_themes()

    # Professional oscilloscope Time/Div and V/Div toolbar
    with dpg.group(horizontal=True, parent=parent):
        dpg.add_text("OSCILLOSCOPE", color=(0, 210, 255))
        if dpg.does_item_exist("font_bold"):
            dpg.bind_item_font(dpg.last_item(), "font_bold")

        dpg.add_spacer(width=4)
        dpg.add_text("Time/Div:", color=(130, 145, 170))
        dpg.add_button(label="<", small=True, callback=lambda: step_scope_time_div(-1))
        dpg.add_combo(
            items=[opt[0] for opt in TIME_DIV_OPTIONS],
            default_value=TIME_DIV_OPTIONS[0][0],
            width=145,
            callback=lambda s, a: set_scope_time_div(a),
            tag="scope_time_div_combo",
        )
        dpg.add_button(label=">", small=True, callback=lambda: step_scope_time_div(1))

        dpg.add_spacer(width=6)
        dpg.add_text("V/Div:", color=(130, 145, 170))
        dpg.add_button(label="<", small=True, callback=lambda: step_scope_v_div(-1))
        dpg.add_combo(
            items=[opt[0] for opt in V_DIV_OPTIONS],
            default_value=V_DIV_OPTIONS[0][0],
            width=155,
            callback=lambda s, a: set_scope_v_div(a),
            tag="scope_v_div_combo",
        )
        dpg.add_button(label=">", small=True, callback=lambda: step_scope_v_div(1))

        dpg.add_spacer(width=6)
        dpg.add_button(label="Auto Y-Fit", small=True, callback=fit_scope_y)
        dpg.add_button(label="Reset", small=True, callback=reset_scope_view)

        dpg.add_spacer(width=4)
        dpg.add_checkbox(label="Y-Lock", default_value=True, callback=toggle_scope_y_lock, tag="scope_lock_checkbox")

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
            label="Time (us)",
            tag="sinewave_xaxis"
        )
        y_axis = dpg.add_plot_axis(
            dpg.mvYAxis,
            label="ADC Amplitude",
            tag="sinewave_yaxis",
            lock_min=True,
            lock_max=True
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
