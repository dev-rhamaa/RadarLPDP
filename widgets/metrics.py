"""Metrics widget for displaying radar telemetry and target detection."""

import dearpygui.dearpygui as dpg


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
            dpg.add_table_column(label="Peak Power (dB)")

            with dpg.table_row():
                dpg.add_text("CH0 (RF Beat)", color=(0, 210, 255))
                dpg.add_text("N/A", tag="ch1_peak_freq")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")
                dpg.add_text("N/A", tag="ch1_peak_mag")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")

            with dpg.table_row():
                dpg.add_text("CH2 (Sync)", color=(255, 184, 0))
                dpg.add_text("N/A", tag="ch2_peak_freq")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")
                dpg.add_text("N/A", tag="ch2_peak_mag")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")

        dpg.add_spacer(height=6)

        # 2. Target Acquisition (>10 MHz / FMCW Beat Detection)
        dpg.add_text("Target Acquisition (>10 MHz Beat):", color=(255, 184, 0))
        with dpg.table(
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True
        ):
            dpg.add_table_column(label="Channel")
            dpg.add_table_column(label="Target Freq (MHz)")
            dpg.add_table_column(label="Target Mag (dB)")

            with dpg.table_row():
                dpg.add_text("CH0", color=(0, 210, 255))
                dpg.add_text("N/A", tag="ch1_target_freq")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")
                dpg.add_text("N/A", tag="ch1_target_mag")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")

            with dpg.table_row():
                dpg.add_text("CH2", color=(255, 184, 0))
                dpg.add_text("N/A", tag="ch2_target_freq")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")
                dpg.add_text("N/A", tag="ch2_target_mag")
                if dpg.does_item_exist("font_mono"):
                    dpg.bind_item_font(dpg.last_item(), "font_mono")
