"""Callback functions for UI updates and event handling.

This module contains all callback functions for updating the UI based on
data from worker threads, handling window resize events, and cleanup operations.
"""

import queue
import time
from collections import deque
from typing import Any, Dict, List, Tuple

import dearpygui.dearpygui as dpg
import numpy as np

from app.external_process import stop_worker
from config import (
    APP_SPACING,
    APP_PADDING,
    THEME_COLORS,
    TARGET_HISTORY_MAX_SIZE,
)
from widgets.PPI import update_sweep_line, add_target_to_plot

# Global UI state
last_known_angle: float = 0.0
target_history: deque = deque(maxlen=TARGET_HISTORY_MAX_SIZE)

def update_ui_from_queues(queues: Dict[str, queue.Queue]) -> None:
    """Check all queues and update UI with new data.
    
    Args:
        queues: Dictionary of queues for different data types
    """
    global last_known_angle, target_history

    # PPI queue - handles sweep and target messages
    try:
        ppi_data = queues['ppi'].get_nowait()
        
        if ppi_data['type'] == 'sweep':
            # Message from angle_worker: update sweep angle and line
            last_known_angle = ppi_data['angle']
            update_sweep_line(last_known_angle)

        elif ppi_data['type'] == 'target':
            # Message from fft_data_worker: add new target at last known angle
            distance = ppi_data['distance']
            new_target = (last_known_angle, distance)
            target_history.append(new_target)  # deque auto-removes oldest
            
            add_target_to_plot(list(target_history))
    except queue.Empty:
        pass

    # FFT and metrics queue
    try:
        fft_data = queues['fft'].get_nowait()
        
        # Skip update if FFT UI doesn't exist, but consume queue
        if not dpg.does_item_exist("fft_status_text"):
            return
            
        status = fft_data.get("status")
        
        if status == "processing":
            dpg.set_value("fft_status_text", "Processing...")
            
        elif status in ["error", "waiting"]:
            dpg.set_value("fft_status_text", fft_data.get("message", "Unknown status"))
            
        elif status == "done":
            dpg.set_value("fft_status_text", f"Updated: {time.strftime('%H:%M:%S')}")
            
            # Update FFT plots
            if dpg.does_item_exist('fft_ch1_series'):
                dpg.set_value(
                    'fft_ch1_series',
                    [fft_data["freqs_ch1"], fft_data["mag_ch1"]]
                )
            if dpg.does_item_exist('fft_ch2_series'):
                dpg.set_value(
                    'fft_ch2_series',
                    [fft_data["freqs_ch2"], fft_data["mag_ch2"]]
                )
            if dpg.does_item_exist("fft_yaxis"):
                dpg.set_axis_limits_auto("fft_yaxis")

            # Update metrics widget
            metrics = fft_data.get("metrics", {})
            _update_channel_metrics("ch1", metrics.get('ch1', {}))
            _update_channel_metrics("ch2", metrics.get('ch2', {}))
            
            # Update target detection (>10 MHz)
            _update_target_detection("ch1", metrics.get('ch1', {}))
            _update_target_detection("ch2", metrics.get('ch2', {}))

            # Update peaks & valleys tables
            ch1 = metrics.get('ch1', {})
            ch2 = metrics.get('ch2', {})
            _update_extrema_table('ch1', ch1.get('peaks', []), ch1.get('valleys', []))
            _update_extrema_table('ch2', ch2.get('peaks', []), ch2.get('valleys', []))
            
            # Update filtered peaks & valleys tables (index > 2000)
            _update_extrema_table('ch1_filtered', ch1.get('filtered_peaks', []), ch1.get('filtered_valleys', []))
            _update_extrema_table('ch2_filtered', ch2.get('filtered_peaks', []), ch2.get('filtered_valleys', []))
    except queue.Empty:
        pass

    # Sinewave queue
    try:
        sinewave_data = queues['sinewave'].get_nowait()
        
        if not dpg.does_item_exist("sinewave_ch1_series"):
            return
            
        if sinewave_data.get("status") == "done":
            time_axis = np.ascontiguousarray(sinewave_data["time_axis"])
            ch1_data = np.ascontiguousarray(sinewave_data["ch1_data"])
            ch2_data = np.ascontiguousarray(sinewave_data["ch2_data"])
            
            dpg.set_value("sinewave_ch1_series", [time_axis, ch1_data])
            dpg.set_value("sinewave_ch2_series", [time_axis, ch2_data])
            
            if dpg.does_item_exist("sinewave_xaxis"):
                dpg.set_axis_limits_auto("sinewave_xaxis")
            if dpg.does_item_exist("sinewave_yaxis"):
                dpg.set_axis_limits_auto("sinewave_yaxis")
    except queue.Empty:
        pass


def _update_channel_metrics(channel_prefix: str, metrics: Dict[str, Any]) -> None:
    """Update channel metrics display.
    
    Args:
        channel_prefix: Channel identifier (e.g., 'ch1', 'ch2')
        metrics: Dictionary containing peak frequency and magnitude
    """
    freq_tag = f"{channel_prefix}_peak_freq"
    mag_tag = f"{channel_prefix}_peak_mag"
    
    if dpg.does_item_exist(freq_tag):
        dpg.set_value(freq_tag, f"{metrics.get('peak_freq', 0.0):.2f}")
    if dpg.does_item_exist(mag_tag):
        dpg.set_value(mag_tag, f"{metrics.get('peak_mag', 0.0):.2f}")


def _update_target_detection(channel_prefix: str, metrics: Dict[str, Any]) -> None:
    """Update target detection display (>10 MHz).
    
    Args:
        channel_prefix: Channel identifier (e.g., 'ch1', 'ch2')
        metrics: Dictionary containing target frequency and magnitude
    """
    freq_tag = f"{channel_prefix}_target_freq"
    mag_tag = f"{channel_prefix}_target_mag"
    
    target_freq = metrics.get('target_freq', 0.0)
    target_mag = metrics.get('target_mag', 0.0)
    
    if dpg.does_item_exist(freq_tag):
        if target_freq > 0:
            # Convert kHz to MHz for display
            dpg.set_value(freq_tag, f"{target_freq / 1000.0:.3f}")
        else:
            dpg.set_value(freq_tag, "N/A")
            
    if dpg.does_item_exist(mag_tag):
        if target_freq > 0:
            dpg.set_value(mag_tag, f"{target_mag:.2f}")
        else:
            dpg.set_value(mag_tag, "N/A")


def _update_extrema_table(
    prefix: str,
    peaks: List[Dict[str, Any]],
    valleys: List[Dict[str, Any]],
    max_rows: int = 5
) -> None:
    """Update peaks and valleys table.
    
    Args:
        prefix: Channel prefix (e.g., 'ch1', 'ch2')
        peaks: List of peak dictionaries
        valleys: List of valley dictionaries
        max_rows: Maximum number of rows to display
    """
    combined = [("peak", p) for p in peaks] + [("valley", v) for v in valleys]
    
    for i in range(max_rows):
        row_index_id = f"{prefix}_ext_{i}_index"
        row_freq_id = f"{prefix}_ext_{i}_freq"
        row_mag_id = f"{prefix}_ext_{i}_mag"
        row_type_id = f"{prefix}_ext_{i}_type"
        
        # Check if all row elements exist
        if not all(dpg.does_item_exist(x) for x in [
            row_index_id, row_freq_id, row_mag_id, row_type_id
        ]):
            continue
            
        if i < len(combined):
            extrema_type, item = combined[i]
            dpg.set_value(row_index_id, str(item.get("index", "-")))
            dpg.set_value(row_freq_id, f"{item.get('freq_khz', 0.0):.2f}")
            dpg.set_value(row_mag_id, f"{item.get('mag_db', 0.0):.2f}")
            dpg.set_value(
                row_type_id,
                "Peak" if extrema_type == "peak" else "Valley"
            )
        else:
            # Clear empty rows
            dpg.set_value(row_index_id, "-")
            dpg.set_value(row_freq_id, "-")
            dpg.set_value(row_mag_id, "-")
            dpg.set_value(row_type_id, "-")


def resize_callback() -> None:
    """Dynamically adjust layout when window is resized."""
    if not dpg.is_dearpygui_running():
        return

    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    # Calculate padding and spacing
    padding = APP_PADDING * 2
    spacing = APP_SPACING

    # Calculate column widths (adaptive if right_column doesn't exist)
    left_exists = dpg.does_item_exist("left_column")
    right_exists = dpg.does_item_exist("right_column")

    if left_exists and right_exists:
        left_col_width = int(viewport_width * 0.7) - spacing
        right_col_width = viewport_width - left_col_width - (spacing * 2)
        dpg.set_item_width("left_column", max(left_col_width, 0))
        dpg.set_item_width("right_column", max(right_col_width, 0))
    elif left_exists:
        dpg.set_item_width("left_column", max(viewport_width - padding, 0))

    # Calculate left column panel heights (adaptive for PPI-only mode)
    available_height_left = viewport_height - padding
    
    if dpg.does_item_exist("ppi_window") and not dpg.does_item_exist("fft_window"):
        # PPI only: use all available height
        dpg.set_item_height("ppi_window", max(available_height_left, 0))
    else:
        # PPI + FFT: split height
        if dpg.does_item_exist("ppi_window") and dpg.does_item_exist("fft_window"):
            ppi_height = int(available_height_left * 0.65) - spacing
            fft_height = available_height_left - ppi_height - spacing
            dpg.set_item_height("ppi_window", max(ppi_height, 0))
            dpg.set_item_height("fft_window", max(fft_height, 0))

    # Calculate right column panel heights (if exists)
    if right_exists:
        available_height_right = viewport_height - padding
        panel_height = (available_height_right - (spacing * 3)) // 4
        
        for tag in [
            "sinewave_window",
            "metrics_window",
            "file_explorer_window",
            "logo_window"
        ]:
            if dpg.does_item_exist(tag):
                dpg.set_item_height(tag, max(panel_height, 0))

def cleanup_and_exit(
    stop_event: Any,
    threads: Dict[str, Any]
) -> None:
    """Safely stop worker threads and close Dear PyGui.
    
    Args:
        stop_event: Threading event to signal shutdown
        threads: Dictionary of worker threads
    """
    print("Stopping worker threads...")
    stop_event.set()
    time.sleep(0.5)
    
    for t in threads.values():
        t.join()
        
    print("All threads stopped. Destroying context.")
    
    # Ensure external process is also stopped
    try:
        stop_worker()
    except Exception as e:
        print(f"[external_worker] stop error: {e}")
        
    dpg.destroy_context()
