"""Data processing module for RF signal analysis.

This module provides functions for loading, processing, and analyzing RF data
from the ADC, including FFT computation, peak detection, and statistical analysis.
"""

import math
import os
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import serial
from numpy.typing import NDArray
from scipy.fft import rfft, rfftfreq
from scipy.signal import find_peaks, get_window, savgol_filter

from config import (
    FILENAME,
    SAMPLE_RATE,
    WORKER_REFRESH_INTERVAL,
    SERIAL_PORT,
    BAUD_RATE,
    SERIAL_TIMEOUT,
    RADAR_MAX_RANGE,
    RADAR_SWEEP_ANGLE_MIN,
    RADAR_SWEEP_ANGLE_MAX,
    FFT_SMOOTHING_ENABLED,
    FFT_SMOOTHING_METHOD,
    FFT_SMOOTHING_WINDOW,
    FFT_SAVGOL_WINDOW,
    FFT_SAVGOL_POLYORDER,
    FFT_MAGNITUDE_MODE,
    FFT_MAGNITUDE_FLOOR_DB,
    FFT_IMPEDANCE_OHMS,
    FFT_MAGNITUDE_FLOOR_DBM,
    TARGET_FREQ_THRESHOLD_KHZ,
    FILTERED_EXTREMA_INDEX_THRESHOLD,
)

# --- Coordinate Conversion Functions ---

def polar_to_cartesian(
    center_x: float,
    center_y: float,
    angle_deg: float,
    radius: float
) -> Tuple[float, float]:
    """Convert polar coordinates to Cartesian coordinates.
    
    Args:
        center_x: X coordinate of the center point
        center_y: Y coordinate of the center point
        angle_deg: Angle in degrees
        radius: Radius from center
        
    Returns:
        Tuple of (x, y) Cartesian coordinates
    """
    angle_rad = math.radians(angle_deg)
    x = center_x + radius * math.cos(angle_rad)
    y = center_y + radius * math.sin(angle_rad)
    return x, y

# --- Signal Analysis Functions ---

def smooth_spectrum(
    magnitudes: NDArray[np.float64],
    window_size: int = 5,
    method: str = "moving_average",
    savgol_window: int = 51,
    savgol_polyorder: int = 3
) -> NDArray[np.float64]:
    """Apply smoothing filter to reduce noise grass in spectrum.
    
    Args:
        magnitudes: Magnitude array to smooth
        window_size: Moving average window size
        method: Smoothing method ('moving_average' or 'savgol')
        savgol_window: Window length for Savitzky-Golay filter (must be odd)
        savgol_polyorder: Polynomial order for Savitzky-Golay filter
        
    Returns:
        Smoothed magnitude array
    """
    n = len(magnitudes)
    if n == 0:
        return magnitudes

    method = (method or "moving_average").lower()

    if method == "savgol":
        if n < 3:
            return magnitudes

        window = min(savgol_window, n)
        if window % 2 == 0:
            window -= 1

        min_window = max(savgol_polyorder + 1, 3)
        if min_window % 2 == 0:
            min_window += 1

        if window < min_window:
            window = min_window

        if window > n:
            window = n if n % 2 == 1 else n - 1

        if window < 3 or window <= savgol_polyorder:
            return magnitudes

        try:
            return savgol_filter(magnitudes, window_length=window, polyorder=savgol_polyorder)
        except ValueError:
            # Fallback to moving average if parameters invalid
            pass

    if window_size <= 1 or n < window_size:
        return magnitudes

    kernel = np.ones(window_size, dtype=np.float64) / window_size
    smoothed = np.convolve(magnitudes, kernel, mode="same")
    return smoothed


def compute_fft(
    channel: NDArray[np.float32],
    sample_rate: int,
    window: str = "hann",
    smooth: bool = True,
    smooth_window: int = 5,
    impedance_ohms: float = 50.0
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute FFT spectrum in calibrated physical RF power (dBm) into 50 ohms load.
    
    Args:
        channel: Input signal data (in Volts or raw 16-bit ADC counts)
        sample_rate: Sample rate in Hz
        window: Window function name (default: 'hann')
        smooth: Apply smoothing to reduce noise (default: True)
        smooth_window: Smoothing window size (default: 5)
        impedance_ohms: RF load impedance in Ohms (default: 50.0)
        
    Returns:
        Tuple of (frequencies_khz, magnitudes_dbm)
    """
    n = len(channel)
    if n == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    # Convert raw 16-bit ADC counts to physical Volts if not already in Volts
    # (PCI-9846H standard range is +/- 1.0 V full scale across 16-bit counts [-32768, 32767])
    arr = np.asarray(channel, dtype=np.float64)
    if np.max(np.abs(arr)) > 2.0:
        v_signal = arr / 32768.0
    else:
        v_signal = arr

    # Window function with coherent gain normalization
    win_sum = float(n)
    if window:
        try:
            w = get_window(window, n, fftbins=True)
            v_signal = v_signal * w
            win_sum = float(np.sum(w))
        except Exception:
            pass

    if win_sum <= 0:
        win_sum = float(n)

    # Compute single-sided real FFT (positive frequencies only)
    fft_result = rfft(v_signal)
    
    # Peak voltage amplitude for each frequency bin:
    # For positive frequencies (k > 0): V_peak = 2.0 * |X[k]| / sum(w)
    # For DC (k = 0): V_peak = |X[0]| / sum(w)
    v_peak = (2.0 / win_sum) * np.abs(fft_result)
    if len(v_peak) > 0:
        v_peak[0] *= 0.5

    # Power in milliwatts into impedance (default 50 ohms):
    # P_watts = (V_rms)^2 / R = (V_peak / sqrt(2))^2 / R = V_peak^2 / (2 * R)
    # P_mW = P_watts * 1000 = (500 / R) * V_peak^2
    # Into 50 ohms: P_mW = 10 * V_peak^2
    # P_dBm = 10 * log10(P_mW) = 10 + 20 * log10(V_peak)
    imp = float(globals().get("FFT_IMPEDANCE_OHMS", impedance_ohms))
    scale_factor = 500.0 / max(imp, 1e-6)
    p_mw = scale_factor * (v_peak ** 2)
    magnitudes_dbm = 10.0 * np.log10(np.maximum(p_mw, 1e-15))

    # Apply smoothing to reduce noise spikes
    if smooth:
        magnitudes_dbm = smooth_spectrum(
            magnitudes_dbm,
            window_size=smooth_window,
            method=FFT_SMOOTHING_METHOD,
            savgol_window=FFT_SAVGOL_WINDOW,
            savgol_polyorder=FFT_SAVGOL_POLYORDER,
        )

    floor_val = globals().get("FFT_MAGNITUDE_FLOOR_DBM", globals().get("FFT_MAGNITUDE_FLOOR_DB", -120.0))
    if floor_val is not None:
        magnitudes_dbm = np.maximum(magnitudes_dbm, floor_val)

    frequencies_khz = rfftfreq(n, d=1.0 / sample_rate) / 1000.0
    return frequencies_khz, magnitudes_dbm


def compute_fft_linear(
    channel: NDArray[np.float32],
    sample_rate: int
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute FFT spectrum magnitude in linear scale (no log, no smoothing).

    Args:
        channel: Input signal data
        sample_rate: Sample rate in Hz

    Returns:
        Tuple of (frequencies_khz, magnitudes_linear)
    """
    n = len(channel)
    if n == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    x = np.asarray(channel, dtype=np.float64)
    fft_result = rfft(x)
    magnitudes = np.abs(fft_result)
    frequencies_khz = rfftfreq(n, d=1.0 / sample_rate) / 1000.0

    return (
        np.ascontiguousarray(frequencies_khz, dtype=np.float64),
        np.ascontiguousarray(magnitudes, dtype=np.float64),
    )

def find_peak_metrics(
    frequencies: NDArray[np.float64],
    magnitudes: NDArray[np.float64]
) -> Tuple[float, float]:
    """Find peak frequency and magnitude from FFT data.
    
    Args:
        frequencies: Frequency array in kHz
        magnitudes: Magnitude array in dBm
        
    Returns:
        Tuple of (peak_frequency, peak_magnitude_dbm)
    """
    if len(magnitudes) == 0:
        return 0.0, 0.0
        
    peak_index = np.argmax(magnitudes)
    peak_freq = float(frequencies[peak_index])
    peak_mag = float(magnitudes[peak_index])
    
    return peak_freq, peak_mag

def find_top_extrema(
    frequencies: NDArray[np.float64],
    magnitudes: NDArray[np.float64],
    n_extrema: int = 3,
    prominence_db: float = 3.0,
    distance_bins: int = 1
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Find top peaks and valleys in the spectrum.
    
    Args:
        frequencies: Frequency array in kHz from compute_fft
        magnitudes: Magnitude array in dBm from compute_fft
        n_extrema: Number of top peaks/valleys to extract
        prominence_db: Prominence threshold for peak detection in dB
        distance_bins: Minimum distance between peaks in FFT bins
        
    Returns:
        Tuple of (peaks, valleys) where each is a list of dicts with
        keys: 'index', 'freq_khz', 'mag_db'
    """
    if len(magnitudes) == 0:
        return [], []

    # Find peaks in magnitude spectrum
    peak_idx, _ = find_peaks(
        magnitudes,
        prominence=prominence_db,
        distance=distance_bins
    )
    
    # Sort peaks by magnitude (highest first)
    peak_idx_sorted = sorted(
        peak_idx,
        key=lambda i: magnitudes[i],
        reverse=True
    )[:n_extrema]
    
    peaks = [
        {
            "index": int(i),
            "freq_khz": float(frequencies[i]),
            "mag_db": float(magnitudes[i])
        }
        for i in peak_idx_sorted
    ]

    # Find valleys by inverting the signal
    inv_magnitudes = -magnitudes
    valley_idx, _ = find_peaks(
        inv_magnitudes,
        prominence=prominence_db,
        distance=distance_bins
    )
    
    # Sort valleys by depth (lowest magnitude first)
    valley_idx_sorted = sorted(
        valley_idx,
        key=lambda i: magnitudes[i]
    )[:n_extrema]
    
    valleys = [
        {
            "index": int(i),
            "freq_khz": float(frequencies[i]),
            "mag_db": float(magnitudes[i])
        }
        for i in valley_idx_sorted
    ]

    return peaks, valleys


def find_target_extrema(
    frequencies: NDArray[np.float64],
    magnitudes: NDArray[np.float64],
    freq_threshold_khz: float = TARGET_FREQ_THRESHOLD_KHZ,
    n_extrema: int = 3,
    prominence_db: float = 3.0,
    distance_bins: int = 1
) -> Tuple[List[Dict[str, Any]], float, float]:
    """Find top peaks above a frequency threshold (for target detection).
    
    This function filters the spectrum to only consider frequencies above
    a specified threshold (default 10 MHz) to identify target signals.
    
    Args:
        frequencies: Frequency array in kHz from compute_fft
        magnitudes: Magnitude array in dBm from compute_fft
        freq_threshold_khz: Frequency threshold in kHz (default: 10,000 kHz = 10 MHz)
        n_extrema: Number of top peaks to extract
        prominence_db: Prominence threshold for peak detection in dB
        distance_bins: Minimum distance between peaks in FFT bins
        
    Returns:
        Tuple of (peaks, highest_peak_freq, highest_peak_mag) where:
        - peaks: List of dicts with keys 'index', 'freq_khz', 'mag_db'
        - highest_peak_freq: Frequency of highest peak in kHz
        - highest_peak_mag: Magnitude of highest peak in dB
    """
    if len(magnitudes) == 0:
        return [], 0.0, 0.0
    
    # Filter frequencies above threshold
    freq_mask = frequencies >= freq_threshold_khz
    
    if not np.any(freq_mask):
        # No frequencies above threshold
        return [], 0.0, 0.0
    
    # Get filtered data
    filtered_freqs = frequencies[freq_mask]
    filtered_mags = magnitudes[freq_mask]
    filtered_indices = np.where(freq_mask)[0]
    
    # Find peaks in filtered spectrum
    peak_idx, _ = find_peaks(
        filtered_mags,
        prominence=prominence_db,
        distance=distance_bins
    )
    
    if len(peak_idx) == 0:
        # No peaks found, return highest point
        max_idx = np.argmax(filtered_mags)
        highest_freq = float(filtered_freqs[max_idx])
        highest_mag = float(filtered_mags[max_idx])
        
        return [
            {
                "index": int(filtered_indices[max_idx]),
                "freq_khz": highest_freq,
                "mag_db": highest_mag
            }
        ], highest_freq, highest_mag
    
    # Sort peaks by magnitude (highest first)
    peak_idx_sorted = sorted(
        peak_idx,
        key=lambda i: filtered_mags[i],
        reverse=True
    )[:n_extrema]
    
    # Build peak list
    peaks = [
        {
            "index": int(filtered_indices[i]),
            "freq_khz": float(filtered_freqs[i]),
            "mag_db": float(filtered_mags[i])
        }
        for i in peak_idx_sorted
    ]
    
    # Get highest peak
    highest_peak = peaks[0] if peaks else {"freq_khz": 0.0, "mag_db": 0.0}
    highest_freq = highest_peak["freq_khz"]
    highest_mag = highest_peak["mag_db"]
    
    return peaks, highest_freq, highest_mag


def find_filtered_extrema(
    frequencies: NDArray[np.float64],
    magnitudes: NDArray[np.float64],
    index_threshold: int = FILTERED_EXTREMA_INDEX_THRESHOLD,
    n_extrema: int = 3,
    prominence_db: float = 3.0,
    distance_bins: int = 1
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Find top peaks and valleys with FFT bin index above threshold.
    
    This function filters the spectrum to only consider FFT bins with
    index > index_threshold (default: 2000) to analyze higher frequency
    components of the signal.
    
    Args:
        frequencies: Frequency array in kHz from compute_fft
        magnitudes: Magnitude array in dBm from compute_fft
        index_threshold: Minimum FFT bin index to consider (default: 2000)
        n_extrema: Number of top peaks/valleys to extract
        prominence_db: Prominence threshold for peak detection in dB
        distance_bins: Minimum distance between peaks in FFT bins
        
    Returns:
        Tuple of (peaks, valleys) where each is a list of dicts with
        keys: 'index', 'freq_khz', 'mag_db'
    """
    if len(magnitudes) == 0:
        return [], []
    
    # Filter by index threshold
    if index_threshold >= len(magnitudes):
        # Threshold too high, no data available
        return [], []
    
    # Get filtered data starting from index_threshold
    filtered_freqs = frequencies[index_threshold:]
    filtered_mags = magnitudes[index_threshold:]
    
    if len(filtered_mags) == 0:
        return [], []
    
    # Find peaks in filtered spectrum
    peak_idx, _ = find_peaks(
        filtered_mags,
        prominence=prominence_db,
        distance=distance_bins
    )
    
    # Sort peaks by magnitude (highest first)
    peak_idx_sorted = sorted(
        peak_idx,
        key=lambda i: filtered_mags[i],
        reverse=True
    )[:n_extrema]
    
    # Build peak list with original indices
    peaks = [
        {
            "index": int(i + index_threshold),
            "freq_khz": float(filtered_freqs[i]),
            "mag_db": float(filtered_mags[i])
        }
        for i in peak_idx_sorted
    ]
    
    # Find valleys by inverting the signal
    inv_magnitudes = -filtered_mags
    valley_idx, _ = find_peaks(
        inv_magnitudes,
        prominence=prominence_db,
        distance=distance_bins
    )
    
    # Sort valleys by depth (lowest magnitude first)
    valley_idx_sorted = sorted(
        valley_idx,
        key=lambda i: filtered_mags[i]
    )[:n_extrema]
    
    # Build valley list with original indices
    valleys = [
        {
            "index": int(i + index_threshold),
            "freq_khz": float(filtered_freqs[i]),
            "mag_db": float(filtered_mags[i])
        }
        for i in valley_idx_sorted
    ]
    
    return peaks, valleys

# --- Signal Processing Helpers ---

def process_raw_channels(
    ch1_data: NDArray[np.float32],
    ch2_data: NDArray[np.float32],
    sample_rate: int
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Process in-memory channel arrays, compute FFT, and return results.
    
    Args:
        ch1_data: Channel 1 signal array (CH0 or CH1)
        ch2_data: Channel 2 signal array (CH2 or CH3)
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (fft_result, metrics)
    """
    if ch1_data is None or len(ch1_data) == 0:
        return None, None

    # Remove DC offset to obtain clean AC RF signals
    ch1_ac = ch1_data - np.mean(ch1_data)
    ch2_ac = ch2_data - np.mean(ch2_data)

    n_samples = len(ch1_ac)

    # Compute FFT with smoothing configuration
    freqs_ch1, mag_ch1 = compute_fft(
        ch1_ac, sample_rate,
        smooth=FFT_SMOOTHING_ENABLED,
        smooth_window=FFT_SMOOTHING_WINDOW
    )
    freqs_ch2, mag_ch2 = compute_fft(
        ch2_ac, sample_rate,
        smooth=FFT_SMOOTHING_ENABLED,
        smooth_window=FFT_SMOOTHING_WINDOW
    )

    display_freqs_ch1, display_mag_ch1 = freqs_ch1, mag_ch1
    display_freqs_ch2, display_mag_ch2 = freqs_ch2, mag_ch2

    if FFT_MAGNITUDE_MODE.lower() == "linear":
        display_freqs_ch1, display_mag_ch1 = compute_fft_linear(ch1_ac, sample_rate)
        display_freqs_ch2, display_mag_ch2 = compute_fft_linear(ch2_ac, sample_rate)

    peak_freq_ch1, peak_mag_ch1 = find_peak_metrics(freqs_ch1, mag_ch1)
    peak_freq_ch2, peak_mag_ch2 = find_peak_metrics(freqs_ch2, mag_ch2)

    # Extract target peaks (>10 MHz by default)
    ch1_target_peaks, target_freq_ch1, target_mag_ch1 = find_target_extrema(
        freqs_ch1, mag_ch1,
        freq_threshold_khz=TARGET_FREQ_THRESHOLD_KHZ,
        n_extrema=5
    )
    ch2_target_peaks, target_freq_ch2, target_mag_ch2 = find_target_extrema(
        freqs_ch2, mag_ch2,
        freq_threshold_khz=TARGET_FREQ_THRESHOLD_KHZ,
        n_extrema=5
    )

    # Extract top peaks and valleys with bin indices
    ch1_peaks, ch1_valleys = find_top_extrema(
        freqs_ch1, mag_ch1,
        n_extrema=5,
        prominence_db=3.0,
        distance_bins=1
    )
    ch2_peaks, ch2_valleys = find_top_extrema(
        freqs_ch2, mag_ch2,
        n_extrema=5,
        prominence_db=3.0,
        distance_bins=1
    )
    
    # Extract filtered peaks and valleys (index > threshold)
    ch1_filtered_peaks, ch1_filtered_valleys = find_filtered_extrema(
        freqs_ch1, mag_ch1,
        index_threshold=FILTERED_EXTREMA_INDEX_THRESHOLD,
        n_extrema=5,
        prominence_db=3.0,
        distance_bins=1
    )
    ch2_filtered_peaks, ch2_filtered_valleys = find_filtered_extrema(
        freqs_ch2, mag_ch2,
        index_threshold=FILTERED_EXTREMA_INDEX_THRESHOLD,
        n_extrema=5,
        prominence_db=3.0,
        distance_bins=1
    )

    fft_result = {
        "status": "done",
        "freqs_ch1": freqs_ch1,
        "mag_ch1": display_mag_ch1,
        "freqs_ch2": freqs_ch2,
        "mag_ch2": display_mag_ch2,
        "n_samples": n_samples,
        "sample_rate": sample_rate,
        "metrics": {
            "ch1": {
                "peak_freq": peak_freq_ch1,
                "peak_mag": peak_mag_ch1,
                "target_freq": target_freq_ch1,
                "target_mag": target_mag_ch1,
                "target_peaks": ch1_target_peaks,
                "peaks": ch1_peaks,
                "valleys": ch1_valleys,
                "filtered_peaks": ch1_filtered_peaks,
                "filtered_valleys": ch1_filtered_valleys
            },
            "ch2": {
                "peak_freq": peak_freq_ch2,
                "peak_mag": peak_mag_ch2,
                "target_freq": target_freq_ch2,
                "target_mag": target_mag_ch2,
                "target_peaks": ch2_target_peaks,
                "peaks": ch2_peaks,
                "valleys": ch2_valleys,
                "filtered_peaks": ch2_filtered_peaks,
                "filtered_valleys": ch2_filtered_valleys
            }
        }
    }
    return fft_result, fft_result["metrics"]



def calculate_target_distance(
    metrics: Optional[Dict[str, Any]],
    *,
    mag_threshold_db: float = 80.0,
    index_min: int = 2_500,
    index_max: int = 4_096,
    channel_mode: str = "auto",
    max_range: float = RADAR_MAX_RANGE,
) -> Optional[float]:
    """Estimate target distance using the strongest qualifying FFT peak.

    Hanya puncak dengan indeks FFT di dalam ``[index_min, index_max]`` yang
    dipertimbangkan. Puncak terkuat dengan magnitudo minimal ``mag_threshold_db``
    dipetakan secara linear ke jarak radar menggunakan rentang indeks tersebut
    dan ``max_range``.

    Args:
        metrics: Dictionary containing channel metrics from
            :func:`process_channel_data`.
        mag_threshold_db: Minimum magnitude (dB) required for a peak.
        index_min: Minimum FFT bin index corresponding to zero distance.
        index_max: Maximum FFT bin index corresponding to ``max_range``.
        channel_mode: One of ``"auto"``, ``"ch1"``, or ``"ch2"`` determining
            which channel(s) to inspect.
        max_range: Maximum radar range in meters used for scaling.

    Returns:
        Estimated distance in meters, or None if no qualifying peak is found.
    """
    if not metrics:
        return None

    if index_max <= index_min:
        return None

    best_candidate: Optional[Tuple[float, int]] = None  # (mag_db, index)

    channel_mode_normalized = channel_mode.lower()
    if channel_mode_normalized == "ch1":
        channel_order = ("ch1",)
    elif channel_mode_normalized == "ch2":
        channel_order = ("ch2",)
    else:
        channel_order = ("ch1", "ch2")

    for channel_key in channel_order:
        channel_metrics = metrics.get(channel_key)
        if not channel_metrics:
            continue

        for peak_list_key in ("filtered_peaks", "peaks"):
            for peak in channel_metrics.get(peak_list_key, []):
                peak_mag = peak.get("mag_db")
                peak_index = peak.get("index")

                if peak_mag is None or peak_index is None:
                    continue
                if peak_mag < mag_threshold_db:
                    continue
                if not (index_min <= peak_index <= index_max):
                    continue

                if best_candidate is None or peak_mag > best_candidate[0]:
                    best_candidate = (float(peak_mag), int(peak_index))

    if not best_candidate:
        return None

    _, peak_index = best_candidate
    clamped_index = max(index_min, min(index_max, peak_index))

    normalized = (clamped_index - index_min) / (index_max - index_min)
    distance = normalized * max_range

    if distance <= 0:
        return None

    return float(min(distance, max_range))

def update_sweep_angle(
    current_angle: float,
    direction: int,
    increment: float
) -> Tuple[float, int]:
    """Update sweep angle for 180-degree back-and-forth motion.
    
    Args:
        current_angle: Current angle in degrees
        direction: Direction of sweep (1 or -1)
        increment: Angle increment per step
        
    Returns:
        Tuple of (new_angle, new_direction)
    """
    new_angle = current_angle + increment * direction
    
    if not (RADAR_SWEEP_ANGLE_MIN <= new_angle <= RADAR_SWEEP_ANGLE_MAX):
        direction *= -1
        new_angle = np.clip(new_angle, RADAR_SWEEP_ANGLE_MIN, RADAR_SWEEP_ANGLE_MAX)
        
    return new_angle, direction

# --- Worker Thread Functions --- #

def angle_worker(ppi_queue: queue.Queue, stop_event: threading.Event) -> None:
    """Read angle data from serial port and send calibrated angles to PPI queue.
    
    This worker reads raw angle data from the serial port, performs direction
    synchronization, and sends calibrated 0-180° angles to the PPI queue.
    
    Args:
        ppi_queue: Queue for sending angle updates
        stop_event: Event to signal worker shutdown
    """
    # Synchronization state
    prev_raw: Optional[float] = None
    prev_dir: Optional[int] = None
    base_offset: float = 0.0
    EPS_MOVEMENT: float = 1e-3  # Movement threshold in degrees

    while not stop_event.is_set():
        try:
            # Coba buka port serial
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT) as ser:
                print(f"Berhasil terhubung ke port serial {SERIAL_PORT}")
                while not stop_event.is_set():
                    if ser.in_waiting > 0:
                        try:
                            # Baca satu baris dari serial, hilangkan whitespace, dan decode
                            line = ser.readline().strip()
                            if not line:
                                continue

                            angle_str = line.decode('utf-8')
                            angle = float(angle_str)
                            
                            # Synchronization and angle translation
                            if prev_raw is None:
                                # First reading - establish baseline
                                base_offset = angle
                                prev_raw = angle
                                prev_dir = None
                                ui_angle = 0.0
                                ppi_queue.put({"type": "sweep", "angle": ui_angle})
                                continue

                            delta = angle - prev_raw
                            if abs(delta) < EPS_MOVEMENT:
                                # Minimal movement, ignore
                                prev_raw = angle
                                continue

                            curr_dir = 1 if delta > 0 else -1

                            # Detect direction change
                            if prev_dir is None:
                                prev_dir = curr_dir
                                base_offset = angle
                            elif curr_dir != prev_dir:
                                # Limit switch hit - reset baseline
                                prev_dir = curr_dir
                                base_offset = angle

                            # Translate to 0-180 based on direction
                            if curr_dir == 1:
                                # Raw increasing => UI 0→180
                                ui_angle = angle - base_offset
                            else:
                                # Raw decreasing => UI 180→0
                                ui_angle = 180.0 - (base_offset - angle)

                            # Clamp to valid UI range
                            ui_angle = max(0.0, min(180.0, ui_angle))

                            ppi_queue.put({"type": "sweep", "angle": ui_angle})
                            prev_raw = angle

                        except ValueError:
                            print(f"Failed to convert serial data to number: '{line.decode('utf-8', errors='ignore')}'")
                        except Exception as read_e:
                            print(f"Error reading serial data: {read_e}")
        
        except serial.SerialException:
            # Report failure once or when disconnected, then wait without spamming
            stop_event.wait(5.0)
        except Exception as e:
            print(f"Unexpected error in angle_worker: {e}")
            stop_event.wait(5.0)

def fft_data_worker(
    fft_queue: queue.Queue,
    ppi_queue: queue.Queue,
    stop_event: threading.Event,
    raw_data_queue: Optional[queue.Queue] = None
) -> None:
    """Compute FFT & metrics from in-memory queue or fallback file monitoring.
    
    Args:
        fft_queue: Queue for FFT results
        ppi_queue: Queue for PPI/target data
        stop_event: Event to signal worker shutdown
        raw_data_queue: Optional in-memory raw acquisition queue
    """
    sr: int = SAMPLE_RATE

    while not stop_event.is_set():
        try:
            # Pure in-memory streaming from C DAQ engine
            if raw_data_queue is not None:
                try:
                    event = raw_data_queue.get(timeout=0.05)
                    ch1_data = event["ch1"]
                    ch2_data = event["ch2"]
                    evt_sr = event.get("sample_rate", sr)

                    fft_result, metrics = process_raw_channels(ch1_data, ch2_data, evt_sr)
                    if fft_result:
                        if fft_queue.full():
                            try:
                                fft_queue.get_nowait()
                            except queue.Empty:
                                pass
                        fft_queue.put_nowait(fft_result)
                        distance = calculate_target_distance(metrics)
                        if distance:
                            if ppi_queue.full():
                                try:
                                    ppi_queue.get_nowait()
                                except queue.Empty:
                                    pass
                            ppi_queue.put_nowait({"type": "target", "distance": distance})
                except queue.Empty:
                    pass
            else:
                time.sleep(0.05)

        except Exception as e:
            print(f"Error in fft_data_worker: {e}")
            time.sleep(0.05)


def sinewave_data_worker(
    result_queue: queue.Queue,
    stop_event: threading.Event,
    raw_data_queue: Optional[queue.Queue] = None
) -> None:
    """Provide waveform data for sinewave plot directly from in-memory queue.
    
    Args:
        result_queue: Queue for sinewave data
        stop_event: Event to signal worker shutdown
        raw_data_queue: Optional in-memory raw acquisition queue
    """
    sr: int = SAMPLE_RATE

    while not stop_event.is_set():
        try:
            # Pure in-memory streaming from C DAQ engine
            if raw_data_queue is not None:
                try:
                    event = raw_data_queue.get(timeout=0.05)
                    ch1_data = event["ch1"]
                    ch2_data = event["ch2"]
                    evt_sr = event.get("sample_rate", sr)
                    n_samples = len(ch1_data)

                    # Subtract DC offset so waveform centers cleanly on 0
                    ch1_centered = ch1_data - np.mean(ch1_data)
                    ch2_centered = ch2_data - np.mean(ch2_data)

                    time_axis_us = np.linspace(
                        0, n_samples / evt_sr, n_samples, endpoint=False
                    ) * 1e6

                    result_data = {
                        "status": "done",
                        "time_axis": time_axis_us,
                        "ch1_data": ch1_centered,
                        "ch2_data": ch2_centered,
                        "n_samples": n_samples
                    }
                    if result_queue.full():
                        try:
                            result_queue.get_nowait()
                        except queue.Empty:
                            pass
                    result_queue.put_nowait(result_data)
                except queue.Empty:
                    pass
            else:
                time.sleep(0.05)

        except Exception as e:
            print(f"Error in sinewave_data_worker: {e}")
            time.sleep(0.05)
