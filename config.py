"""Configuration module for Radar LPDP application.

This module contains all configuration constants and settings for the radar system,
including hardware parameters, file paths, and UI settings.
"""

import os
from pathlib import Path
from typing import Dict, Tuple

# --- Project Paths ---

PROJECT_ROOT: Path = Path(__file__).parent.absolute()
"""Root directory of the project."""

# --- Native C DAQ Hardware Configuration ---

C_DAQ_ENABLED: bool = True
"""Whether to initialize and run the embedded C DAQ engine via ctypes."""

# --- Data Acquisition Configuration ---

# Hardware Parameters (matching ADLink PCI-9846H & FMCW Specifications)
SAMPLE_RATE: int = 20_000_000
"""ADC sample rate in Hz (20 MS/s)."""

NYQUIST_FREQ_HZ: float = SAMPLE_RATE / 2.0
"""Nyquist limit frequency in Hz (10 MHz)."""

NYQUIST_FREQ_KHZ: float = NYQUIST_FREQ_HZ / 1000.0
"""Nyquist limit frequency in kHz (10,000 kHz = 10 MHz)."""

BUFFER_SAMPLES: int = 20_000
"""Number of samples per acquisition buffer (20,000 samples = 1 ms @ 20 MHz)."""

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

# Target Detection Configuration
TARGET_HISTORY_MAX_SIZE: int = 50
"""Maximum number of targets to keep in history."""

TARGET_FREQ_THRESHOLD_KHZ: float = 30.0
"""Minimum frequency threshold for target detection in kHz (30 kHz = 90 m)."""

TARGET_FREQ_MAX_KHZ: float = 5000.0
"""Maximum frequency threshold for target detection in kHz (5000 kHz = 5 MHz = 15 km)."""

TARGET_MAG_THRESHOLD_DBM: float = -80.0
"""Magnitude threshold for target detection in dBm."""

FILTERED_EXTREMA_INDEX_THRESHOLD: int = 30
"""FFT bin index threshold for filtered extrema analysis (30 bins = 30 kHz)."""

# --- Servo Motor & Serial Port Configuration (KYDAS4801A) ---

# Default port adapts to OS; can be overridden with SERVO_COM_PORT or RADAR_SERIAL_PORT
DEFAULT_SERIAL_PORT: str = "COM13" if os.name == "nt" else "/dev/ttyUSB0"
SERIAL_PORT: str = os.getenv("RADAR_SERIAL_PORT", os.getenv("SERVO_COM_PORT", DEFAULT_SERIAL_PORT))
"""Serial port for KYDAS4801A servo position controller (default: COM13)."""

BAUD_RATE: int = 115200
"""Serial baud rate for KYDAS4801A servo communication (115200 bps)."""

# KYDAS4801A Servo parameters.
# Titik tengah (90 deg) TIDAK di-hardcode: servo_controller mengambilnya dari posisi motor
# saat aplikasi pertama kali terhubung. Semua target dihitung relatif terhadap titik itu.
# Skala hasil kalibrasi percobaan: 130.000 counts per 60 deg. Arah: counts positif = kiri
# (sudut mengecil), counts negatif = kanan. Nilai datasheet (encoder 2500 ppr x4, gearbox 80:1)
# adalah 800_000 / 360 = 2222.22 counts/deg.
SERVO_COUNTS_PER_DEG: float = 130_000 / 60.0   # ~2166.67 counts per derajat antena
SERVO_POSITION_TOLERANCE: int = 150     # counts
SERVO_POLL_INTERVAL: float = 0.08       # seconds (~12.5 Hz update rate)

# --- UI Display Configuration ---

FONT_PATH_UI: str = "C:/Windows/Fonts/segoeui.ttf"
FONT_PATH_UI_BOLD: str = "C:/Windows/Fonts/segoeuib.ttf"
FONT_PATH_MONO: str = "C:/Windows/Fonts/consola.ttf"

"""System fonts used by the UI.

Segoe UI has no glyph for box-drawing (U+2500..), arrows (U+2794) or emoji, and
Consolas has no arrows/emoji: DPG renders those as '?'. Use plain ASCII
('|', '->', '-') or the safe symbols U+25CF (●) / U+2022 (•) in UI text.
"""

APP_SPACING: int = 8
"""Spacing between UI elements in pixels."""

# Color Theme - calm dark palette. Each accent has ONE meaning:
#   accent (mint)   -> CH0 signal, radar beam, primary/positive action
#   accent_amber    -> CH2 signal
#   accent_violet   -> UI selection/highlight (menus, sliders, active frames)
#   danger (coral)  -> targets, STOP, error states
#   success (green) -> RUNNING / healthy status
THEME_COLORS: Dict[str, Tuple[int, int, int, int]] = {
    "background": (15, 18, 26, 255),        # App background
    "card_bg": (22, 26, 36, 255),           # Card surface
    "card_border": (38, 44, 58, 255),       # Hairline card border
    "surface_hi": (32, 37, 50, 255),        # Raised controls (buttons, inputs)
    "surface_hover": (42, 48, 64, 255),
    "grid_lines": (120, 135, 165, 28),      # Plot grid / PPI reticle
    "text": (226, 232, 240, 255),           # Primary text
    "text_muted": (128, 138, 160, 255),     # Labels, axis text
    "text_faint": (82, 92, 112, 255),       # Separators, hints
    "accent": (94, 234, 212, 255),          # Mint
    "accent_amber": (251, 191, 114, 255),   # Amber
    "accent_violet": (139, 146, 240, 255),  # Violet
    "success": (74, 222, 128, 255),
    "danger": (248, 113, 113, 255),
    "plot_bg": (18, 21, 30, 255),           # Plot area, slightly darker than card
}
"""Color palette for the application theme.

Colors are in RGBA format (Red, Green, Blue, Alpha).
"""

# --- Radar Configuration ---

RADAR_MAX_RANGE: float = 15.0
"""Maximum radar range in kilometers (15 km)."""

RADAR_SWEEP_ANGLE_MIN: float = 30.0
"""Minimum sweep angle in degrees (30.0 deg sector limit)."""

RADAR_SWEEP_ANGLE_MAX: float = 150.0
"""Maximum sweep angle in degrees (150.0 deg sector limit)."""
