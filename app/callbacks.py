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
    TARGET_FREQ_THRESHOLD_KHZ,
)
from widgets.PPI import update_sweep_line, add_target_to_plot

# Global UI state
last_known_angle: float = 0.0
target_history: deque = deque(maxlen=TARGET_HISTORY_MAX_SIZE)

# Header Telemetry tracking
_frame_count: int = 0
_last_fps_calc: float = time.time()
_current_fps: float = 0.0

# Interactive Zoom & Axis limits state
_pending_axis_unlocks: Dict[str, Tuple[int, bool]] = {}
_fft_initial_fitted: bool = False
_sinewave_initial_fitted: bool = False


def request_axis_zoom(axis: str, vmin: float, vmax: float, lock_after: bool = False) -> None:
    """Safely apply axis limits and schedule unlock so user interaction is preserved."""
    if not dpg.does_item_exist(axis):
        return
    dpg.configure_item(axis, lock_min=False, lock_max=False)
    dpg.set_axis_limits(axis, vmin, vmax)
    _pending_axis_unlocks[axis] = (2, lock_after)


def process_pending_unlocks() -> None:
    """Release axis lock after ImPlot renders the new limits to enable mouse pan/zoom."""
    to_delete = []
    for axis, (count, lock_after) in list(_pending_axis_unlocks.items()):
        if not dpg.does_item_exist(axis):
            to_delete.append(axis)
            continue
        if count <= 1:
            dpg.set_axis_limits_auto(axis)
            if lock_after:
                dpg.configure_item(axis, lock_min=True, lock_max=True)
            to_delete.append(axis)
        else:
            _pending_axis_unlocks[axis] = (count - 1, lock_after)
    for axis in to_delete:
        del _pending_axis_unlocks[axis]


# Oscilloscope V/Div and Time/Div definitions (10 div horizontal, 8 div vertical)
TIME_DIV_OPTIONS = [
    ("100 us/div (1 ms)", 100.0),
    ("50 us/div (500 us)", 50.0),
    ("25 us/div (250 us)", 25.0),
    ("10 us/div (100 us)", 10.0),
    ("5 us/div (50 us)", 5.0),
    ("2 us/div (20 us)", 2.0),
    ("1 us/div (10 us)", 1.0),
    ("0.5 us/div (5 us)", 0.5),
    ("0.2 us/div (2 us)", 0.2),
]

V_DIV_OPTIONS = [
    ("250 mV/div (+/-1.0V)", 250.0 * 32.768),
    ("200 mV/div (+/-800mV)", 200.0 * 32.768),
    ("125 mV/div (+/-500mV)", 125.0 * 32.768),
    ("100 mV/div (+/-400mV)", 100.0 * 32.768),
    ("50 mV/div (+/-200mV)", 50.0 * 32.768),
    ("25 mV/div (+/-100mV)", 25.0 * 32.768),
    ("10 mV/div (+/-40mV)", 10.0 * 32.768),
    ("5 mV/div (+/-20mV)", 5.0 * 32.768),
    ("1 mV/div (+/-4mV)", 1.0 * 32.768),
]

_current_time_div_idx = 0
_current_v_div_idx = 0


def apply_scope_divs() -> None:
    """Apply current Time/Div and V/Div to the oscilloscope plot axes."""
    global _current_time_div_idx, _current_v_div_idx
    if dpg.does_item_exist("sinewave_xaxis"):
        time_div_us = TIME_DIV_OPTIONS[_current_time_div_idx][1]
        request_axis_zoom("sinewave_xaxis", 0.0, float(10.0 * time_div_us))
    if dpg.does_item_exist("sinewave_yaxis"):
        v_div_counts = V_DIV_OPTIONS[_current_v_div_idx][1]
        v_max = float(4.0 * v_div_counts)
        request_axis_zoom("sinewave_yaxis", -v_max, v_max, lock_after=True)
    if dpg.does_item_exist("scope_time_div_combo"):
        dpg.set_value("scope_time_div_combo", TIME_DIV_OPTIONS[_current_time_div_idx][0])
    if dpg.does_item_exist("scope_v_div_combo"):
        dpg.set_value("scope_v_div_combo", V_DIV_OPTIONS[_current_v_div_idx][0])


def set_scope_time_div(time_div_label: str) -> None:
    """Set Time/Div by label from combo box."""
    global _current_time_div_idx
    for idx, (lbl, _) in enumerate(TIME_DIV_OPTIONS):
        if lbl == time_div_label:
            _current_time_div_idx = idx
            break
    apply_scope_divs()


def set_scope_v_div(v_div_label: str) -> None:
    """Set V/Div by label from combo box."""
    global _current_v_div_idx
    for idx, (lbl, _) in enumerate(V_DIV_OPTIONS):
        if lbl == v_div_label:
            _current_v_div_idx = idx
            break
    apply_scope_divs()


def step_scope_time_div(direction: int) -> None:
    """Step Time/Div: direction > 0 to zoom in (smaller time/div), < 0 to zoom out."""
    global _current_time_div_idx
    new_idx = max(0, min(len(TIME_DIV_OPTIONS) - 1, _current_time_div_idx + direction))
    _current_time_div_idx = new_idx
    apply_scope_divs()


def step_scope_v_div(direction: int) -> None:
    """Step V/Div: direction > 0 to zoom in (smaller v/div), < 0 to zoom out."""
    global _current_v_div_idx
    new_idx = max(0, min(len(V_DIV_OPTIONS) - 1, _current_v_div_idx + direction))
    _current_v_div_idx = new_idx
    apply_scope_divs()


def set_scope_timebase(span_us: float) -> None:
    """Set oscilloscope horizontal timebase span (µs), anchored from 0 µs."""
    if not dpg.does_item_exist("sinewave_xaxis"):
        return
    request_axis_zoom("sinewave_xaxis", 0.0, float(span_us))


def zoom_scope_step(factor: float) -> None:
    """Zoom in (factor < 1) or zoom out (factor > 1) horizontally on oscilloscope."""
    if not dpg.does_item_exist("sinewave_xaxis"):
        return
    limits = dpg.get_axis_limits("sinewave_xaxis")
    cur_span = max(limits[1] - limits[0], 1.0)
    new_span = min(max(cur_span * factor, 1.0), 1000.0)
    center = (limits[0] + limits[1]) / 2.0
    new_min = max(0.0, center - new_span / 2.0)
    new_max = min(1000.0, new_min + new_span)
    if new_max - new_min < new_span and new_max >= 1000.0:
        new_min = max(0.0, 1000.0 - new_span)
    request_axis_zoom("sinewave_xaxis", new_min, new_max)


def fit_scope_y() -> None:
    """Auto-fit oscilloscope vertical amplitude to current active signal peaks."""
    if not dpg.does_item_exist("sinewave_ch1_series") or not dpg.does_item_exist("sinewave_yaxis"):
        return
    data = dpg.get_value("sinewave_ch1_series")
    if data and len(data) > 1 and len(data[1]) > 0:
        y_vals = data[1]
        y_min = float(min(y_vals))
        y_max = float(max(y_vals))
        span = max(abs(y_max - y_min), 100.0)
        margin = span * 0.15
        request_axis_zoom("sinewave_yaxis", y_min - margin, y_max + margin, lock_after=True)
    else:
        request_axis_zoom("sinewave_yaxis", -35000.0, 35000.0, lock_after=True)


def reset_scope_view() -> None:
    """Reset oscilloscope to standard 100 us/div (1 ms) and 250 mV/div (+/-1.0V)."""
    global _current_time_div_idx, _current_v_div_idx
    _current_time_div_idx = 0
    _current_v_div_idx = 0
    apply_scope_divs()


def toggle_scope_y_lock(sender, app_data) -> None:
    """Toggle whether mouse wheel zooms X-only (locked Y) or both X and Y."""
    if not dpg.does_item_exist("sinewave_yaxis"):
        return
    is_locked = bool(app_data)
    dpg.configure_item("sinewave_yaxis", lock_min=is_locked, lock_max=is_locked)


def set_fft_span(span_khz: float) -> None:
    """Set FFT frequency span (0 to span_khz)."""
    if not dpg.does_item_exist("fft_xaxis"):
        return
    request_axis_zoom("fft_xaxis", 0.0, float(span_khz))


def zoom_fft_step(factor: float) -> None:
    """Zoom in (factor < 1) or zoom out (factor > 1) on frequency spectrum."""
    if not dpg.does_item_exist("fft_xaxis"):
        return
    limits = dpg.get_axis_limits("fft_xaxis")
    cur_span = max(limits[1] - limits[0], 10.0)
    new_span = min(max(cur_span * factor, 10.0), float(TARGET_FREQ_THRESHOLD_KHZ))
    center = (limits[0] + limits[1]) / 2.0
    new_min = max(0.0, center - new_span / 2.0)
    new_max = min(float(TARGET_FREQ_THRESHOLD_KHZ), new_min + new_span)
    if new_max - new_min < new_span and new_max >= float(TARGET_FREQ_THRESHOLD_KHZ):
        new_min = max(0.0, float(TARGET_FREQ_THRESHOLD_KHZ) - new_span)
    request_axis_zoom("fft_xaxis", new_min, new_max)


def fit_fft_y() -> None:
    """Auto-fit magnitude dB scale to current spectrum peak and noise floor."""
    if not dpg.does_item_exist("fft_ch1_series") or not dpg.does_item_exist("fft_yaxis"):
        return
    data = dpg.get_value("fft_ch1_series")
    if data and len(data) > 1 and len(data[1]) > 0:
        y_vals = data[1]
        y_min = float(min(y_vals))
        y_max = float(max(y_vals))
        margin = max(abs(y_max - y_min) * 0.1, 5.0)
        request_axis_zoom("fft_yaxis", max(y_min - margin, -140.0), min(y_max + margin, 20.0), lock_after=True)
    else:
        request_axis_zoom("fft_yaxis", -110.0, 10.0, lock_after=True)


def reset_fft_view() -> None:
    """Reset FFT to full 10 MHz span and -110 to +10 dB."""
    request_axis_zoom("fft_xaxis", 0.0, float(TARGET_FREQ_THRESHOLD_KHZ))
    request_axis_zoom("fft_yaxis", -110.0, 10.0, lock_after=True)


def toggle_fft_y_lock(sender, app_data) -> None:
    """Toggle whether mouse wheel zooms Frequency-only (locked dB) or both."""
    if not dpg.does_item_exist("fft_yaxis"):
        return
    is_locked = bool(app_data)
    dpg.configure_item("fft_yaxis", lock_min=is_locked, lock_max=is_locked)



def update_ui_from_queues(queues: Dict[str, queue.Queue]) -> None:
    """Check all queues and update UI with new data.
    
    Args:
        queues: Dictionary of queues for different data types
    """
    global last_known_angle, target_history, _frame_count, _last_fps_calc, _current_fps
    global _fft_initial_fitted, _sinewave_initial_fitted

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

    if fft_data is not None and dpg.does_item_exist("fft_plot"):
        status = fft_data.get("status")
        
        if status == "processing":
            if dpg.does_item_exist("fft_status_text"):
                dpg.set_value("fft_status_text", "Processing...")
            
        elif status in ["error", "waiting"]:
            if dpg.does_item_exist("fft_status_text"):
                dpg.set_value("fft_status_text", fft_data.get("message", "Unknown status"))
            
        elif status == "done":
            if dpg.does_item_exist("fft_status_text"):
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

            # One-time initial fit on startup
            if not _fft_initial_fitted and dpg.does_item_exist("fft_xaxis") and dpg.does_item_exist("fft_yaxis"):
                request_axis_zoom("fft_xaxis", 0.0, float(TARGET_FREQ_THRESHOLD_KHZ))
                request_axis_zoom("fft_yaxis", -110.0, 10.0, lock_after=True)
                _fft_initial_fitted = True

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
            
            # One-time initial fit on startup
            if not _sinewave_initial_fitted and dpg.does_item_exist("sinewave_xaxis") and dpg.does_item_exist("sinewave_yaxis"):
                request_axis_zoom("sinewave_xaxis", 0.0, 1000.0)
                request_axis_zoom("sinewave_yaxis", -35000.0, 35000.0, lock_after=True)
                _sinewave_initial_fitted = True

    # Process pending unlocks for programmatic zoom requests
    process_pending_unlocks()


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
