"""Data processing module for RF signal analysis.

This module provides functions for loading, processing, and analyzing RF data
from the ADC, including FFT computation, peak detection, and statistical analysis.
"""

import math
import os
import queue
import struct
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import serial
from numpy.typing import NDArray
from scipy import stats as sp_stats
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

# --- Data Loading Functions ---

def load_and_process_data(
    filepath: str,
    sample_rate: int
) -> Tuple[Optional[NDArray[np.float32]], Optional[NDArray[np.float32]], Optional[int], int]:
    """Load binary data file, separate channels, and remove DC offset.
    
    Args:
        filepath: Path to the binary data file
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (ch1_data, ch2_data, n_samples, sample_rate)
        Returns (None, None, None, sample_rate) on error
    """
    try:
        if not os.path.exists(filepath):
            return None, None, None, sample_rate

        with open(filepath, "rb") as f:
            data = f.read()
        
        if not data:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32), 0, sample_rate

        # Ensure even byte length for uint16 unpacking
        if len(data) % 2 != 0:
            data = data[:-1]

        values = np.array(
            struct.unpack(f"<{len(data)//2}H", data),
            dtype=np.float32
        )

        # Ensure even number of samples for 2-channel deinterleaving
        if len(values) % 2 != 0:
            values = values[:-1]
            
        # Deinterleave channels: CH1 (even indices), CH2 (odd indices)
        ch1 = values[::2]
        ch2 = values[1::2]
        
        # Remove DC offset
        ch1 -= np.mean(ch1)
        ch2 -= np.mean(ch2)
        
        return ch1, ch2, len(ch1), sample_rate
        
    except Exception as e:
        print(f"Error reading or processing file {filepath}: {e}")
        return None, None, None, sample_rate

# --- FFT and Spectral Analysis Functions ---

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
    smooth_window: int = 5
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Compute FFT spectrum and convert magnitude to dB.
    
    Args:
        channel: Input signal data
        sample_rate: Sample rate in Hz
        window: Window function name (default: 'hann')
        smooth: Apply smoothing to reduce noise (default: True)
        smooth_window: Smoothing window size (default: 5)
        
    Returns:
        Tuple of (frequencies_khz, magnitudes_db)
    """
    n = len(channel)
    if n == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    x = np.asarray(channel, dtype=np.float64)
    
    # Apply window function to reduce spectral leakage
    if window:
        try:
            w = get_window(window, n, fftbins=True)
            x = x * w
        except Exception:
            pass  # Fallback without window if invalid

    # Compute real FFT (positive frequencies only)
    fft_result = rfft(x)
    magnitudes = np.abs(fft_result)

    # Convert to dB scale, avoiding log(0)
    magnitudes_db = 20.0 * np.log10(magnitudes + 1e-12)
    
    # Apply smoothing to reduce noise spikes
    if smooth:
        magnitudes_db = smooth_spectrum(
            magnitudes_db,
            window_size=smooth_window,
            method=FFT_SMOOTHING_METHOD,
            savgol_window=FFT_SAVGOL_WINDOW,
            savgol_polyorder=FFT_SAVGOL_POLYORDER,
        )

    if FFT_MAGNITUDE_FLOOR_DB is not None:
        magnitudes_db = np.maximum(magnitudes_db, FFT_MAGNITUDE_FLOOR_DB)

    # Frequencies in kHz
    frequencies_khz = rfftfreq(n, d=1.0 / sample_rate) / 1000.0
    
    return frequencies_khz, magnitudes_db


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
        magnitudes: Magnitude array in dB
        
    Returns:
        Tuple of (peak_frequency, peak_magnitude)
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
        magnitudes: Magnitude array in dB from compute_fft
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
        magnitudes: Magnitude array in dB from compute_fft
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
        magnitudes: Magnitude array in dB from compute_fft
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

# --- Statistical Analysis Functions ---

def compute_basic_stats(arr: NDArray) -> Dict[str, float]:
    """Compute basic statistics for signal data.
    
    Args:
        arr: Input signal array
        
    Returns:
        Dictionary containing mean, std, min, max, and rms values
    """
    if arr is None or len(arr) == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "rms": 0.0}
        
    desc = sp_stats.describe(np.asarray(arr, dtype=np.float64), ddof=0)
    mean = float(desc.mean)
    var = float(desc.variance) if desc.variance is not None else float(np.var(arr))
    std = float(np.sqrt(var))
    min_val, max_val = map(float, desc.minmax)
    rms = float(np.sqrt(np.mean(np.square(arr))))
    
    return {
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
        "rms": rms
    }

# REMOVED: compute_fft_analysis() - redundant with process_channel_data()
# Use _compute_channel_metrics() for internal analysis needs

def generate_time_axis_s(
    n_samples: int,
    sample_rate: float
) -> NDArray[np.float64]:
    """Generate time axis in seconds.
    
    Args:
        n_samples: Number of samples
        sample_rate: Sample rate in Hz
        
    Returns:
        Time axis array in seconds (C-contiguous, float64)
    """
    if n_samples <= 0 or sample_rate <= 0:
        return np.array([], dtype=np.float64)
        
    time_axis = np.linspace(
        0,
        n_samples / sample_rate,
        n_samples,
        endpoint=False
    )
    return np.ascontiguousarray(time_axis, dtype=np.float64)

def _compute_single_channel_analysis(
    channel: NDArray,
    sample_rate: int
) -> Dict[str, Any]:
    """Internal helper: compute FFT analysis for a single channel.
    
    Args:
        channel: Input signal data
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary with frequencies, magnitudes, and peak info
    """
    if channel is None or len(channel) == 0:
        return {
            "frequencies": np.array([], dtype=np.float64),
            "magnitudes": np.array([], dtype=np.float64),
            "max_freq": 0.0,
            "max_mag": 0.0,
        }
    
    freqs_khz, mags_db = compute_fft(
        channel, sample_rate,
        smooth=FFT_SMOOTHING_ENABLED,
        smooth_window=FFT_SMOOTHING_WINDOW
    )
    peak_freq, peak_mag = find_peak_metrics(freqs_khz, mags_db)
    
    peaks, valleys = find_top_extrema(freqs_khz, mags_db, n_extrema=5)
    
    return {
        "frequencies": np.ascontiguousarray(freqs_khz, dtype=np.float64),
        "magnitudes": np.ascontiguousarray(mags_db, dtype=np.float64),
        "peak_frequencies": np.ascontiguousarray(
            [p["freq_khz"] for p in peaks], dtype=np.float64
        ),
        "peak_magnitudes": np.ascontiguousarray(
            [p["mag_db"] for p in peaks], dtype=np.float64
        ),
        "max_freq": float(peak_freq),
        "max_mag": float(peak_mag),
    }

def analyze_loaded_data(
    ch1: NDArray,
    ch2: NDArray,
    sample_rate: float,
    n_samples: Optional[int] = None,
    duration_s: Optional[float] = None
) -> Dict[str, Any]:
    """Perform complete analysis on loaded channel data.
    
    Args:
        ch1: Channel 1 data
        ch2: Channel 2 data
        sample_rate: Sample rate in Hz
        n_samples: Number of samples (auto-detected if None)
        duration_s: Duration in seconds (auto-calculated if None)
        
    Returns:
        Dictionary containing FFT analysis, statistics, and file info
    """
    # Use internal helper for FFT analysis
    ch1_fft = _compute_single_channel_analysis(ch1, int(sample_rate))
    ch2_fft = _compute_single_channel_analysis(ch2, int(sample_rate))
    ch1_stats = compute_basic_stats(ch1)
    ch2_stats = compute_basic_stats(ch2)
    
    if n_samples is None:
        n_samples = len(ch1) if ch1 is not None else 0
    if duration_s is None and sample_rate > 0:
        duration_s = n_samples / sample_rate
        
    return {
        "ch1_fft": ch1_fft,
        "ch2_fft": ch2_fft,
        "ch1_stats": ch1_stats,
        "ch2_stats": ch2_stats,
        "file_info": {
            "duration": float(duration_s or 0.0),
            "n_samples": int(n_samples or 0),
            "sample_rate": float(sample_rate or 0.0),
        },
    }

def load_file_and_prepare(
    filepath: str,
    sample_rate: float
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load binary file and prepare data structure for UI.
    
    Args:
        filepath: Path to binary data file
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (data_dict, error_message)
        data_dict is None if error occurs
    """
    ch1_data, ch2_data, n_samples, sr = load_and_process_data(
        filepath, int(sample_rate)
    )
    
    if ch1_data is None or n_samples is None or n_samples <= 0:
        return None, "File not found or empty"
        
    time_axis = generate_time_axis_s(n_samples, sr)
    
    data_dict = {
        "ch1": np.ascontiguousarray(ch1_data, dtype=np.float64),
        "ch2": np.ascontiguousarray(ch2_data, dtype=np.float64),
        "time_axis": time_axis,
        "n_samples": n_samples,
        "sample_rate": sr,
        "duration": (n_samples / sr) if sr else 0.0,
    }
    
    return data_dict, None

def process_channel_data(
    filepath: str,
    sample_rate: int
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Load data from file, process FFT, and return results.
    
    Args:
        filepath: Path to binary data file
        sample_rate: Sample rate in Hz
        
    Returns:
        Tuple of (fft_result, metrics)
        Returns (None, None) on error
    """
    ch1_data, ch2_data, n_samples, _ = load_and_process_data(filepath, sample_rate)
    if ch1_data is None or n_samples <= 0:
        return None, None

    # Compute FFT with smoothing configuration
    freqs_ch1, mag_ch1 = compute_fft(
        ch1_data, sample_rate,
        smooth=FFT_SMOOTHING_ENABLED,
        smooth_window=FFT_SMOOTHING_WINDOW
    )
    freqs_ch2, mag_ch2 = compute_fft(
        ch2_data, sample_rate,
        smooth=FFT_SMOOTHING_ENABLED,
        smooth_window=FFT_SMOOTHING_WINDOW
    )

    display_freqs_ch1, display_mag_ch1 = freqs_ch1, mag_ch1
    display_freqs_ch2, display_mag_ch2 = freqs_ch2, mag_ch2

    if FFT_MAGNITUDE_MODE.lower() == "linear":
        display_freqs_ch1, display_mag_ch1 = compute_fft_linear(ch1_data, sample_rate)
        display_freqs_ch2, display_mag_ch2 = compute_fft_linear(ch2_data, sample_rate)

    peak_freq_ch1, peak_mag_ch1 = find_peak_metrics(freqs_ch1, mag_ch1)
    peak_freq_ch2, peak_mag_ch2 = find_peak_metrics(freqs_ch2, mag_ch2)

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
                "peaks": ch1_peaks,
                "valleys": ch1_valleys,
                "filtered_peaks": ch1_filtered_peaks,
                "filtered_valleys": ch1_filtered_valleys
            },
            "ch2": {
                "peak_freq": peak_freq_ch2,
                "peak_mag": peak_mag_ch2,
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
    mag_threshold_db: float = 75.0,
    index_min: int = 500,
    index_max: int = 4_096,
    channel_mode: str = "ch1",
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
            print(f"Failed to connect to {SERIAL_PORT}. Check connection. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error in angle_worker: {e}")
            time.sleep(5)

def fft_data_worker(
    fft_queue: queue.Queue,
    ppi_queue: queue.Queue,
    stop_event: threading.Event
) -> None:
    """Monitor file, compute FFT & metrics, and send data to queues.
    
    This worker monitors the data file for changes, computes FFT analysis,
    calculates target distance, and sends results to FFT and PPI queues.
    
    Args:
        fft_queue: Queue for FFT results
        ppi_queue: Queue for PPI/target data
        stop_event: Event to signal worker shutdown
    """
    last_modified_time: float = 0.0
    filepath: str = FILENAME
    sr: int = SAMPLE_RATE

    while not stop_event.is_set():
        try:
            if os.path.exists(filepath):
                modified_time = os.path.getmtime(filepath)
                if modified_time != last_modified_time:
                    last_modified_time = modified_time
                    fft_queue.put({"status": "processing"})
                    
                    fft_result, metrics = process_channel_data(filepath, sr)
                    if fft_result:
                        fft_queue.put(fft_result)
                        
                        distance = calculate_target_distance(metrics)
                        if distance:
                            # Send target detection event WITHOUT angle info
                            ppi_queue.put({"type": "target", "distance": distance})
            
            # Sleep briefly to avoid CPU overload
            time.sleep(0.1)

        except Exception as e:
            print(f"Error in fft_data_worker: {e}")

def sinewave_data_worker(
    result_queue: queue.Queue,
    stop_event: threading.Event
) -> None:
    """Monitor data file for sinewave plot updates.
    
    Args:
        result_queue: Queue for sinewave data
        stop_event: Event to signal worker shutdown
    """
    last_modified_time: float = 0.0
    filepath: str = FILENAME
    sr: int = SAMPLE_RATE

    while not stop_event.is_set():
        try:
            if os.path.exists(filepath):
                modified_time = os.path.getmtime(filepath)
                if modified_time != last_modified_time:
                    last_modified_time = modified_time
                    
                    ch1_data, ch2_data, n_samples, _ = load_and_process_data(filepath, sr)
                    if ch1_data is None or n_samples == 0:
                        continue
                    
                    # Convert time axis to microseconds (µs)
                    time_axis_us = np.linspace(
                        0, n_samples / sr, n_samples, endpoint=False
                    ) * 1e6
                    
                    result_data = {
                        "status": "done",
                        "time_axis": time_axis_us,
                        "ch1_data": ch1_data,
                        "ch2_data": ch2_data
                    }
                    result_queue.put(result_data)

        except Exception as e:
            print(f"Error in sinewave_data_worker: {e}")
        
        # Use consistent refresh interval
        time.sleep(WORKER_REFRESH_INTERVAL)
