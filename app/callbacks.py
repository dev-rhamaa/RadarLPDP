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

# Header Telemetry tracking
_frame_count: int = 0
_last_fps_calc: float = time.time()
_current_fps: float = 0.0


def update_ui_from_queues(queues: Dict[str, queue.Queue]) -> None:
    """Check all queues and update UI with new data.
    
    Args:
        queues: Dictionary of queues for different data types
    """
    global last_known_angle, target_history, _frame_count, _last_fps_calc, _current_fps

    # 0. Live Top Header Telemetry (1 Hz update rate)
    _frame_count += 1
    now = time.time()
    if now - _last_fps_calc >= 1.0:
        _current_fps = _frame_count / max(now - _last_fps_calc, 0.001)
        _frame_count = 0
        _last_fps_calc = now

        if dpg.does_item_exist("header_fps_count"):
            dpg.set_value("header_fps_count", f"{_current_fps:.1f} FPS")

        if dpg.does_item_exist("header_system_time"):
            dpg.set_value("header_system_time", time.strftime("%H:%M:%S"))

        try:
            from app.setup import get_active_daq_engine
            engine = get_active_daq_engine()
            if engine and hasattr(engine, "event_count") and dpg.does_item_exist("header_event_count"):
                dpg.set_value("header_event_count", f"{engine.event_count:,} EVT")
        except Exception:
            pass

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

    # FFT and metrics queue - drain to latest
    fft_data = None
    try:
        while True:
            fft_data = queues['fft'].get_nowait()
    except queue.Empty:
        pass

    if fft_data is not None and dpg.does_item_exist("fft_status_text"):
        status = fft_data.get("status")
        
        if status == "processing":
            dpg.set_value("fft_status_text", "Processing...")
            
        elif status in ["error", "waiting"]:
            dpg.set_value("fft_status_text", fft_data.get("message", "Unknown status"))
            
        elif status == "done":
            dpg.set_value("fft_status_text", f"Live DAQ: {time.strftime('%H:%M:%S')}")
            
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

    # Sinewave queue - drain to latest
    sinewave_data = None
    try:
        while True:
            sinewave_data = queues['sinewave'].get_nowait()
    except queue.Empty:
        pass

    if sinewave_data is not None and dpg.does_item_exist("sinewave_ch1_series"):
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


def resize_callback() -> None:
    """Dynamically adjust layout when window is resized."""
    if not dpg.is_dearpygui_running():
        return

    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    # Calculate padding, spacing, and header bar height
    padding = APP_PADDING * 2
    spacing = APP_SPACING
    header_height = 42 if dpg.does_item_exist("top_header_bar") else 0

    # Calculate column widths (adaptive if right_column doesn't exist)
    left_exists = dpg.does_item_exist("left_column")
    right_exists = dpg.does_item_exist("right_column")

    if left_exists and right_exists:
        left_col_width = int(viewport_width * 0.68) - spacing
        right_col_width = viewport_width - left_col_width - (spacing * 2) - 8
        dpg.set_item_width("left_column", max(left_col_width, 0))
        dpg.set_item_width("right_column", max(right_col_width, 0))
    elif left_exists:
        dpg.set_item_width("left_column", max(viewport_width - padding, 0))

    # Available vertical space for workspace cards
    available_height = viewport_height - header_height - padding - spacing - 4

    # Calculate left column panel heights (PPI 58% / FFT 42%)
    if dpg.does_item_exist("ppi_window") and not dpg.does_item_exist("fft_window"):
        dpg.set_item_height("ppi_window", max(available_height, 0))
    elif dpg.does_item_exist("ppi_window") and dpg.does_item_exist("fft_window"):
        ppi_height = int(available_height * 0.58) - spacing
        fft_height = available_height - ppi_height - spacing
        dpg.set_item_height("ppi_window", max(ppi_height, 0))
        dpg.set_item_height("fft_window", max(fft_height, 0))

    # Calculate right column panel heights (3 functional widgets)
    if right_exists:
        logo_height = 80 if dpg.does_item_exist("logo_window") else 0
        remaining_h = available_height - logo_height - (spacing * 2)
        
        sinewave_height = int(remaining_h * 0.52)
        metrics_height = remaining_h - sinewave_height

        if dpg.does_item_exist("sinewave_window"):
            dpg.set_item_height("sinewave_window", max(sinewave_height, 0))
        if dpg.does_item_exist("metrics_window"):
            dpg.set_item_height("metrics_window", max(metrics_height, 0))
        if dpg.does_item_exist("logo_window"):
            dpg.set_item_height("logo_window", max(logo_height, 0))

def cleanup_and_exit(
    stop_event: Any,
    threads: Dict[str, Any]
) -> None:
    """Safely stop worker threads, release DAQ hardware, and close Dear PyGui.
    
    Args:
        stop_event: Threading event to signal shutdown
        threads: Dictionary of worker threads and engines
    """
    print("Stopping worker threads...")
    stop_event.set()
    
    for name, t in threads.items():
        if hasattr(t, "stop"):
            t.stop()
        elif hasattr(t, "join"):
            t.join(timeout=1.0)
        
    print("All threads stopped. Destroying context.")
    dpg.destroy_context()
