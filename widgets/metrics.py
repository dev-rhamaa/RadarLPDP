"""Metrics widget for displaying frequency analysis results.

This module provides UI components for displaying peak frequency metrics
and extrema (peaks/valleys) for both channels.
"""

from typing import Optional

import dearpygui.dearpygui as dpg


def create_metrics_widget(
    parent: int | str,
    width: int,
    height: int
) -> None:
    """Create widget for displaying frequency metrics.
    
    Args:
        parent: Parent container ID or tag
        width: Widget width in pixels
        height: Widget height in pixels
    """
    with dpg.group(parent=parent):
        dpg.add_text("Frequency Metrics")
        
        # Main metrics table
        with dpg.table(
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True
        ):
            dpg.add_table_column(label="Channel")
            dpg.add_table_column(label="Peak Frequency (kHz)")
            dpg.add_table_column(label="Peak Magnitude (dB)")

            # Channel 1 row
            with dpg.table_row():
                dpg.add_text("CH1 (Odd)")
                dpg.add_text("N/A", tag="ch1_peak_freq")
                dpg.add_text("N/A", tag="ch1_peak_mag")

            # Channel 2 row
            with dpg.table_row():
                dpg.add_text("CH2 (Even)")
                dpg.add_text("N/A", tag="ch2_peak_freq")
                dpg.add_text("N/A", tag="ch2_peak_mag")
        
        # Target Detection table (>10 MHz)
        dpg.add_spacer(height=6)
        dpg.add_text("Target Detection (>10 MHz)", color=(255, 200, 0))
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

            # Channel 1 target
            with dpg.table_row():
                dpg.add_text("CH1")
                dpg.add_text("N/A", tag="ch1_target_freq")
                dpg.add_text("N/A", tag="ch1_target_mag")

            # Channel 2 target
            with dpg.table_row():
                dpg.add_text("CH2")
                dpg.add_text("N/A", tag="ch2_target_freq")
                dpg.add_text("N/A", tag="ch2_target_mag")

        # Channel 1 extrema table
        dpg.add_spacer(height=6)
        dpg.add_text("Top Peaks & Valleys (CH1)")
        _create_extrema_table("ch1", num_rows=5)

        # Channel 2 extrema table
        dpg.add_spacer(height=6)
        dpg.add_text("Top Peaks & Valleys (CH2)")
        _create_extrema_table("ch2", num_rows=5)
        
        # Filtered extrema table (Index > 2000)
        dpg.add_spacer(height=6)
        dpg.add_text("Filtered Peaks & Valleys (Index > 2000) - CH1", color=(100, 200, 255))
        _create_extrema_table("ch1_filtered", num_rows=5)
        
        dpg.add_spacer(height=6)
        dpg.add_text("Filtered Peaks & Valleys (Index > 2000) - CH2", color=(100, 200, 255))
        _create_extrema_table("ch2_filtered", num_rows=5)


def _create_extrema_table(channel_prefix: str, num_rows: int = 5) -> None:
    """Create table for displaying peaks and valleys.
    
    Args:
        channel_prefix: Channel identifier prefix (e.g., 'ch1', 'ch2')
        num_rows: Number of rows to create
    """
    with dpg.table(
        header_row=True,
        borders_innerH=True,
        borders_outerH=True,
        borders_innerV=True,
        borders_outerV=True
    ):
        dpg.add_table_column(label="#")
        dpg.add_table_column(label="Index")
        dpg.add_table_column(label="Freq (kHz)")
        dpg.add_table_column(label="Mag (dB)")
        dpg.add_table_column(label="Type")

        for i in range(num_rows):
            with dpg.table_row():
                dpg.add_text(f"{i+1}")
                dpg.add_text("-", tag=f"{channel_prefix}_ext_{i}_index")
                dpg.add_text("-", tag=f"{channel_prefix}_ext_{i}_freq")
                dpg.add_text("-", tag=f"{channel_prefix}_ext_{i}_mag")
                dpg.add_text("-", tag=f"{channel_prefix}_ext_{i}_type")
