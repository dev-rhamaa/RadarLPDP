"""Metrics widget for displaying radar telemetry and target detection."""

import dearpygui.dearpygui as dpg

from app.fonts import FONT_MONO, bind_last_item_font


def create_metrics_widget(parent: int | str, width: int, height: int) -> None:
    """Create clean, functional telemetry and target detection tables."""
    with dpg.group(parent=parent):
        # 1. Primary Channel Beat Frequency & Power
        dpg.add_text("Channel Telemetry (Beat Frequency & Power):", color=(180, 200, 230))
        with dpg.table(
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True
        ):
            dpg.add_table_column(label="Channel")
            dpg.add_table_column(label="Peak Freq (kHz)")
            dpg.add_table_column(label="Peak Power (dBm)")

            with dpg.table_row():
                dpg.add_text("CH0 (RF Beat)", color=(0, 210, 255))
                dpg.add_text("N/A", tag="ch1_peak_freq")
                bind_last_item_font(FONT_MONO)
                dpg.add_text("N/A", tag="ch1_peak_mag")
                bind_last_item_font(FONT_MONO)

            with dpg.table_row():
                dpg.add_text("CH2 (Sync)", color=(255, 184, 0))
                dpg.add_text("N/A", tag="ch2_peak_freq")
                bind_last_item_font(FONT_MONO)
                dpg.add_text("N/A", tag="ch2_peak_mag")
                bind_last_item_font(FONT_MONO)

        dpg.add_spacer(height=6)

        # 2. Target Detection (30 kHz - 5 MHz • Max 15 km • Nyquist: 10 MHz)
        dpg.add_text("Target Detection (30 kHz - 5 MHz • Max 15 km):", color=(255, 184, 0))
        with dpg.table(
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True
        ):
            dpg.add_table_column(label="Channel")
            dpg.add_table_column(label="Beat Freq (kHz)")
            dpg.add_table_column(label="Est. Range (km)")
            dpg.add_table_column(label="Power (dBm)")

            with dpg.table_row():
                dpg.add_text("CH0", color=(0, 210, 255))
                dpg.add_text("N/A", tag="ch1_target_freq")
                bind_last_item_font(FONT_MONO)
                dpg.add_text("N/A", tag="ch1_target_range")
                bind_last_item_font(FONT_MONO)
                dpg.add_text("N/A", tag="ch1_target_mag")
                bind_last_item_font(FONT_MONO)

            with dpg.table_row():
                dpg.add_text("CH2", color=(255, 184, 0))
                dpg.add_text("N/A", tag="ch2_target_freq")
                bind_last_item_font(FONT_MONO)
                dpg.add_text("N/A", tag="ch2_target_range")
                bind_last_item_font(FONT_MONO)
                dpg.add_text("N/A", tag="ch2_target_mag")
                bind_last_item_font(FONT_MONO)
