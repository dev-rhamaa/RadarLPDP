"""Configuration module for Radar LPDP application.

This module contains all configuration constants and settings for the radar system,
including hardware parameters, file paths, and UI settings.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

# --- Project Paths ---

PROJECT_ROOT: Path = Path(__file__).parent.absolute()
"""Root directory of the project."""

# --- Native C DAQ Hardware Configuration ---

C_DAQ_ENABLED: bool = True
"""Whether to initialize and run the embedded C DAQ engine via ctypes."""

C_DAQ_WRITE_LIVE_BIN: bool = False
"""Disabled: Streaming is direct in-memory without buffering to .bin file."""

C_DAQ_BATCH_LOG_ENABLED: bool = False
"""Disabled: No batch buffering to disk, data is streamed directly to UI."""

C_DAQ_BATCH_MAX_EVENTS: int = 1000
"""Number of events to accumulate before flushing batch log to disk (if enabled)."""

# --- Data Acquisition Configuration ---

FILENAME_BASE: str = "live/live_acquisition_ui.bin"
"""Relative path to the live data file (fallback / legacy mode)."""

FILENAME: str = str(PROJECT_ROOT / FILENAME_BASE)
"""Absolute path to the live data file."""

# Hardware Parameters (matching cadgetdatanew.c)
# Hardware Parameters (matching cadgetdatanew.c & FMCW Specifications)
SAMPLE_RATE: int = 20_000_000
"""ADC sample rate in Hz (20 MHz)."""

NYQUIST_FREQ_HZ: float = SAMPLE_RATE / 2.0
"""Nyquist limit frequency in Hz (10 MHz)."""

NYQUIST_FREQ_KHZ: float = NYQUIST_FREQ_HZ / 1000.0
"""Nyquist limit frequency in kHz (10,000 kHz = 10 MHz)."""

BUFFER_SAMPLES: int = 20_000
"""Number of samples per acquisition buffer matching cadgetdatanew.c (20,000 samples = 1 ms @ 20 MHz)."""

NUM_CHANNELS: int = 2
"""Number of ADC channels (CH0 and CH2)."""

# --- FMCW Radar Technical Specifications (Ground Surveillance Portable FMCW) ---
FMCW_CARRIER_FREQ_HZ: float = 5.6e9
"""C-Band carrier center frequency (5600 MHz)."""

FMCW_BANDWIDTH_HZ: float = 50_000_000.0
"""FMCW sweep bandwidth (50 MHz, from 5600 +/- 25 MHz)."""

FMCW_CHIRP_TIME_S: float = 0.001
"""Chirp sweep time (1 ms = 1000 Hz sweep repetition rate)."""

FMCW_TX_POWER_W: float = 5.0
"""SSPA output power in Watts (5 W = 37 dBm max)."""

FMCW_TX_POWER_DBM: float = 37.0
"""Transmit power in dBm."""

FMCW_RX_LNA_SENSITIVITY_DBM: float = -40.0
"""Rx LNA sensitivity threshold in dBm (-40 dBm)."""

FMCW_BEAT_MIN_KHZ: float = 30.0
"""Minimum Rx beat frequency output in kHz (30 kHz = 90 meters range)."""

FMCW_BEAT_MAX_KHZ: float = 5000.0
"""Maximum Rx beat frequency output in kHz (5000 kHz = 5 MHz = 15 km range)."""

FMCW_RANGE_FACTOR_M_PER_KHZ: float = 3.0
"""FMCW distance factor: 3.0 meters per kHz of beat frequency (delta_R = c*T / (2*B))."""

# FFT Processing Configuration
FFT_SMOOTHING_ENABLED: bool = True
"""Enable FFT spectrum smoothing to reduce noise."""

FFT_SMOOTHING_WINDOW: int = 11
"""Moving average smoothing window (fallback for other methods)."""

FFT_SMOOTHING_METHOD: str = "savgol"
"""Smoothing method to apply ('moving_average' or 'savgol')."""

FFT_SAVGOL_WINDOW: int = 51
"""Savitzky-Golay window length (must be odd)."""

FFT_SAVGOL_POLYORDER: int = 3
"""Savitzky-Golay polynomial order."""

FFT_MAGNITUDE_MODE: str = "dbm"
"""Output magnitude scale for FFT ('linear' or 'dbm')."""

FFT_IMPEDANCE_OHMS: float = 50.0
"""RF load impedance in Ohms for calibrated dBm power calculation (Standard 50 Ohm)."""

FFT_MAGNITUDE_FLOOR_DBM: float = -120.0
"""Clamp FFT magnitude to this floor to suppress noise grass (dBm)."""
FFT_MAGNITUDE_FLOOR_DB: float = -120.0
"""Backward compatibility alias for FFT_MAGNITUDE_FLOOR_DBM."""

# Worker Configuration
POLLING_INTERVAL: float = 0.5
"""File polling interval in seconds (deprecated, kept for compatibility)."""

WORKER_REFRESH_INTERVAL: float = 0.05
"""UI refresh interval in seconds (~20 FPS)."""

# Target Detection Configuration
TARGET_HISTORY_MAX_SIZE: int = 50
"""Maximum number of targets to keep in history."""

TARGET_FREQ_THRESHOLD_KHZ: float = 10_000.0
"""Frequency threshold for target detection in kHz (10 MHz)."""
TARGET_FREQ_THRESHOLD_KHZ: float = 30.0
"""Minimum frequency threshold for target detection in kHz (30 kHz = 90 m)."""

FILTERED_EXTREMA_INDEX_THRESHOLD: int = 2000
"""FFT bin index threshold for filtered extrema analysis."""
TARGET_FREQ_MAX_KHZ: float = 5000.0
"""Maximum frequency threshold for target detection in kHz (5000 kHz = 5 MHz = 15 km)."""

TARGET_MAG_THRESHOLD_DBM: float = -80.0
"""Magnitude threshold for target detection in dBm."""

FILTERED_EXTREMA_INDEX_THRESHOLD: int = 30
"""FFT bin index threshold for filtered extrema analysis (30 bins = 30 kHz)."""

# --- Serial Port Configuration ---

# Default port adapts to OS; can be overridden with RADAR_SERIAL_PORT environment variable
DEFAULT_SERIAL_PORT: str = "COM3" if os.name == "nt" else "/dev/ttyUSB0"
SERIAL_PORT: str = os.getenv("RADAR_SERIAL_PORT", DEFAULT_SERIAL_PORT)
"""Serial port for ESP32/Arduino communication."""

BAUD_RATE: int = 115200
"""Serial baud rate (must match Arduino code)."""

SERIAL_TIMEOUT: float = 1.0
"""Serial read timeout in seconds."""

# --- UI Display Configuration ---

APP_SPACING: int = 8
"""Spacing between UI elements in pixels."""

APP_PADDING: int = 8
"""Padding for UI elements in pixels."""

# Color Theme - Tactical Dark Aerospace Radar Palette
THEME_COLORS: Dict[str, Tuple[int, int, int, int]] = {
    "background": (11, 15, 23, 255),        # Deep Slate Navy
    "card_bg": (18, 24, 37, 255),           # Card Container Dark
    "card_border": (36, 48, 71, 230),       # Subtle Card Border
    "scan_area": (14, 26, 38, 160),         # PPI Scan Sector
    "grid_lines": (36, 52, 76, 140),        # PPI & Plot Grid Reticle
    "text": (240, 246, 255, 255),           # Crisp Primary Text
    "text_muted": (130, 145, 170, 255),     # Muted Slate Text
    "accent": (0, 210, 255, 255),           # Cyber Tech Cyan
    "accent_green": (0, 255, 157, 255),     # Radar Phosphor Green (Sweep)
    "accent_amber": (255, 184, 0, 255),     # Signal Amber / CH2
    "target": (255, 59, 48, 255),           # Tactical Target Crimson
    "plot_bg": (9, 13, 20, 255),            # Oscilloscope Dark Screen
}
"""Color palette for the application theme.

Colors are in RGBA format (Red, Green, Blue, Alpha).
"""

# --- Radar Configuration ---

RADAR_MAX_RANGE: float = 15.0
"""Maximum radar range in meters."""
"""Maximum radar range in kilometers (15 km)."""

RADAR_MIN_RANGE: float = 0.09
"""Minimum radar range in kilometers (90 meters = 30 kHz beat frequency)."""

RADAR_SWEEP_ANGLE_MIN: float = 0.0
"""Minimum sweep angle in degrees."""

RADAR_SWEEP_ANGLE_MAX: float = 180.0
"""Maximum sweep angle in degrees."""
