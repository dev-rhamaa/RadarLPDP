"""Callback functions for UI updates and event handling.

This module contains all callback functions for updating the UI based on
data from worker threads, handling window resize events, and cleanup operations.
"""

import queue
import time
from collections import deque
from typing import Any, Dict, Tuple

import dearpygui.dearpygui as dpg
import numpy as np

from app import settings
from config import (
    APP_SPACING,
    TARGET_HISTORY_MAX_SIZE,
    NYQUIST_FREQ_KHZ,
    FMCW_RANGE_FACTOR_M_PER_KHZ,
)
from widgets.PPI import update_sweep_line, add_target_to_plot

# Global UI state
last_known_angle: float = 90.0
target_history: deque = deque(maxlen=TARGET_HISTORY_MAX_SIZE)


def set_target_history_size(size: int) -> None:
    """Resize the PPI target trail, keeping the most recent targets."""
    global target_history
    size = max(1, int(size))
    if target_history.maxlen != size:
        target_history = deque(target_history, maxlen=size)
        add_target_to_plot(list(target_history))


def clear_targets() -> None:
    target_history.clear()
    add_target_to_plot([])

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
    ("0.1 us/div (1 us)", 0.1),
    ("0.05 us/div (500 ns)", 0.05),
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
    if dpg.does_item_exist("sinewave_xaxis"):
        time_div_us = TIME_DIV_OPTIONS[_current_time_div_idx][1]
        request_axis_zoom("sinewave_xaxis", 0.0, float(10.0 * time_div_us))
    if dpg.does_item_exist("sinewave_yaxis"):
        v_div_counts = V_DIV_OPTIONS[_current_v_div_idx][1]
        v_max = float(4.0 * v_div_counts)
        request_axis_zoom("sinewave_yaxis", -v_max, v_max, lock_after=bool(settings.get("scope.y_lock")))
    # Sync menu check marks and the card read-out
    for idx in range(len(TIME_DIV_OPTIONS)):
        if dpg.does_item_exist(f"menu_tdiv_{idx}"):
            dpg.set_value(f"menu_tdiv_{idx}", idx == _current_time_div_idx)
    for idx in range(len(V_DIV_OPTIONS)):
        if dpg.does_item_exist(f"menu_vdiv_{idx}"):
            dpg.set_value(f"menu_vdiv_{idx}", idx == _current_v_div_idx)
    if dpg.does_item_exist("scope_div_readout"):
        t_lbl = TIME_DIV_OPTIONS[_current_time_div_idx][0].split(" (")[0]
        v_lbl = V_DIV_OPTIONS[_current_v_div_idx][0].split(" (")[0]
        dpg.set_value("scope_div_readout", f"{t_lbl}  ·  {v_lbl}")


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
        request_axis_zoom("sinewave_yaxis", y_min - margin, y_max + margin, lock_after=bool(settings.get("scope.y_lock")))
    else:
        request_axis_zoom("sinewave_yaxis", -35000.0, 35000.0, lock_after=bool(settings.get("scope.y_lock")))


def _option_index(options, label: str, fallback: int = 0) -> int:
    for idx, (lbl, _) in enumerate(options):
        if lbl == label:
            return idx
    return fallback


def reset_scope_view() -> None:
    """Reset oscilloscope to the Time/Div and V/Div saved in Settings."""
    global _current_time_div_idx, _current_v_div_idx
    _current_time_div_idx = _option_index(TIME_DIV_OPTIONS, settings.get("scope.time_div"))
    _current_v_div_idx = _option_index(V_DIV_OPTIONS, settings.get("scope.v_div"))
    apply_scope_divs()


def set_scope_y_lock(is_locked: bool) -> None:
    """Lock Y so the mouse wheel zooms time only (True) or both axes (False)."""
    if dpg.does_item_exist("sinewave_yaxis"):
        dpg.configure_item("sinewave_yaxis", lock_min=bool(is_locked), lock_max=bool(is_locked))


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
    new_span = min(max(cur_span * factor, 10.0), float(NYQUIST_FREQ_KHZ))
    center = (limits[0] + limits[1]) / 2.0
    new_min = max(0.0, center - new_span / 2.0)
    new_max = min(float(NYQUIST_FREQ_KHZ), new_min + new_span)
    if new_max - new_min < new_span and new_max >= float(NYQUIST_FREQ_KHZ):
        new_min = max(0.0, float(NYQUIST_FREQ_KHZ) - new_span)
    request_axis_zoom("fft_xaxis", new_min, new_max)


def fit_fft_y() -> None:
    """Auto-fit magnitude dBm scale to current spectrum peak and noise floor."""
    if not dpg.does_item_exist("fft_ch1_series") or not dpg.does_item_exist("fft_yaxis"):
        return
    data = dpg.get_value("fft_ch1_series")
    if data and len(data) > 1 and len(data[1]) > 0:
        y_vals = data[1]
        y_min = float(min(y_vals))
        y_max = float(max(y_vals))
        margin = max(abs(y_max - y_min) * 0.1, 5.0)
        request_axis_zoom("fft_yaxis", max(y_min - margin, -130.0), min(y_max + margin, 15.0), lock_after=bool(settings.get("fft.y_lock")))
    else:
        request_axis_zoom("fft_yaxis", -110.0, 10.0, lock_after=bool(settings.get("fft.y_lock")))


def reset_fft_view() -> None:
    """Reset FFT to the span and dBm range saved in Settings."""
    span = min(float(settings.get("fft.span_khz")), float(NYQUIST_FREQ_KHZ))
    request_axis_zoom("fft_xaxis", 0.0, span)
    request_axis_zoom("fft_yaxis", float(settings.get("fft.y_min")), float(settings.get("fft.y_max")),
                      lock_after=bool(settings.get("fft.y_lock")))


def set_fft_y_lock(is_locked: bool) -> None:
    """Lock dBm so the mouse wheel zooms frequency only (True) or both axes (False)."""
    if dpg.does_item_exist("fft_yaxis"):
        dpg.configure_item("fft_yaxis", lock_min=bool(is_locked), lock_max=bool(is_locked))



def update_ui_from_queues(queues: Dict[str, queue.Queue]) -> None:
    """Check all queues and update UI with new data.
    
    Args:
        queues: Dictionary of queues for different data types
    """
    global last_known_angle, _frame_count, _last_fps_calc, _current_fps
    global _fft_initial_fitted, _sinewave_initial_fitted

    # 0. Live Top Header Telemetry (1 Hz update rate)
    _frame_count += 1
    now = time.time()
    if now - _last_fps_calc >= 1.0:
        _current_fps = _frame_count / max(now - _last_fps_calc, 0.001)
        _frame_count = 0
        _last_fps_calc = now

        if dpg.does_item_exist("header_fps_count"):
            dpg.set_value("header_fps_count", f"{_current_fps:.0f} FPS")

        if dpg.does_item_exist("header_system_time"):
            dpg.set_value("header_system_time", time.strftime("%H:%M:%S"))

        try:
            from app.setup import get_active_daq_engine
            engine = get_active_daq_engine()
            if engine and hasattr(engine, "event_count") and dpg.does_item_exist("header_event_count"):
                dpg.set_value("header_event_count", f"{engine.event_count:,} evt")
        except Exception:
            pass

    # PPI queue - drain all pending messages for zero-latency servo angle tracking
    try:
        while True:
            ppi_data = queues['ppi'].get_nowait()
            if ppi_data['type'] == 'sweep':
                last_known_angle = ppi_data['angle']
                update_sweep_line(last_known_angle)
            elif ppi_data['type'] == 'target':
                distance = ppi_data['distance']
                new_target = (last_known_angle, distance)
                target_history.append(new_target)
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

            # One-time initial fit on startup (Full Nyquist 10 MHz)
            if not _fft_initial_fitted and dpg.does_item_exist("fft_xaxis") and dpg.does_item_exist("fft_yaxis"):
                reset_fft_view()
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
                reset_scope_view()
                _sinewave_initial_fitted = True
    # Live cursor tracking for Frequency-to-Range conversion on hover
    if dpg.does_item_exist("fft_plot") and dpg.does_item_exist("fft_cursor_readout"):
        if dpg.is_item_hovered("fft_plot"):
            try:
                pos = dpg.get_plot_mouse_pos()
                f_khz = float(pos[0])
                if f_khz >= 0.0:
                    r_m = f_khz * FMCW_RANGE_FACTOR_M_PER_KHZ
                    if r_m < 1000.0:
                        dpg.set_value("fft_cursor_readout", f"{f_khz:,.1f} kHz  =  {r_m:.0f} m")
                    else:
                        dpg.set_value("fft_cursor_readout", f"{f_khz:,.1f} kHz  =  {r_m / 1000.0:.2f} km")
            except Exception:
                pass

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
    """Update target detection display (30 kHz - 5 MHz FMCW beat, max 15 km).
    
    Args:
        channel_prefix: Channel identifier (e.g., 'ch1', 'ch2')
        metrics: Dictionary containing target frequency, range, and magnitude
    """
    freq_tag = f"{channel_prefix}_target_freq"
    range_tag = f"{channel_prefix}_target_range"
    mag_tag = f"{channel_prefix}_target_mag"
    
    target_freq = metrics.get('target_freq', 0.0)
    target_mag = metrics.get('target_mag', 0.0)
    
    has_target = target_freq >= 30.0
    dist_km = (target_freq * FMCW_RANGE_FACTOR_M_PER_KHZ) / 1000.0

    if dpg.does_item_exist(freq_tag):
        dpg.set_value(freq_tag, f"{target_freq:.1f}" if has_target else "—")
    if dpg.does_item_exist(range_tag):
        dpg.set_value(range_tag, f"{dist_km:.2f}" if has_target else "—")
    if dpg.does_item_exist(mag_tag):
        dpg.set_value(mag_tag, f"{target_mag:.2f}" if has_target else "—")
    if channel_prefix == "ch1" and dpg.does_item_exist("metric_range_big"):
        dpg.set_value("metric_range_big", f"{dist_km:.2f}" if has_target else "—")


# Workspace layout: column -> [(panel window tag, share of flexible height, fixed px or 0)]
LEFT_PANELS = [("ppi_window", 0.60, 0), ("fft_window", 0.40, 0)]
RIGHT_PANELS = [("sinewave_window", 0.44, 0), ("metrics_window", 0.56, 0), ("logo_window", 0.0, 64)]
MENU_BAR_HEIGHT = 30
WINDOW_PADDING = 10  # matches mvStyleVar_WindowPadding in app/setup.py
LEFT_COLUMN_SHARE = 0.66


def _visible(panels):
    return [p for p in panels if dpg.does_item_exist(p[0]) and dpg.is_item_shown(p[0])]


def _layout_column(column_tag: str, panels, width: int, avail_h: int) -> None:
    """Size the visible panels of one column. Fixed-height panels keep their size; the
    flexible ones share what is left. The bottom panel uses height=-1 when flexible so the
    column always ends exactly at the window edge."""
    visible = _visible(panels)
    dpg.configure_item(column_tag, show=bool(visible))
    if not visible:
        return
    dpg.set_item_width(column_tag, max(width, 0))
    fixed_total = sum(px for _, _, px in visible if px) + APP_SPACING * (len(visible) - 1)
    flex = [p for p in visible if not p[2]]
    share_total = sum(share for _, share, _ in flex) or 1.0
    flex_h = max(avail_h - fixed_total, 0)
    for tag, share, px in visible:
        dpg.set_item_width(tag, max(width, 0))
        if px:
            dpg.set_item_height(tag, px)
        elif tag == visible[-1][0]:
            dpg.set_item_height(tag, -1)
        else:
            dpg.set_item_height(tag, max(int(flex_h * share / share_total), 80))


def resize_callback() -> None:
    """Lay out the two workspace columns, skipping panels hidden via the View menu."""
    if not dpg.is_dearpygui_running() or not dpg.does_item_exist("left_column"):
        return

    content_w = dpg.get_viewport_client_width() - WINDOW_PADDING * 2
    avail_h = dpg.get_viewport_client_height() - MENU_BAR_HEIGHT - WINDOW_PADDING * 2

    left_on = bool(_visible(LEFT_PANELS))
    right_on = bool(_visible(RIGHT_PANELS))
    if left_on and right_on:
        left_w = int(content_w * LEFT_COLUMN_SHARE)
        right_w = content_w - left_w - APP_SPACING
    else:
        left_w = right_w = content_w

    _layout_column("left_column", LEFT_PANELS, left_w, avail_h)
    _layout_column("right_column", RIGHT_PANELS, right_w, avail_h)


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
