"""Unit tests for config module."""

import pytest
from pathlib import Path
import config


@pytest.mark.unit
class TestConfig:
    """Verify configuration parameters and constants."""

    def test_project_root_exists(self):
        """Verify PROJECT_ROOT exists and points to project directory."""
        assert isinstance(config.PROJECT_ROOT, Path)
        assert config.PROJECT_ROOT.exists()
        assert (config.PROJECT_ROOT / "main.py").exists()

    def test_hardware_parameters(self):
        """Verify critical hardware acquisition constants."""
        assert config.SAMPLE_RATE == 20_000_000
        assert config.BUFFER_SAMPLES == 20_000
        assert config.NUM_CHANNELS == 2

    def test_radar_sweep_and_range_limits(self):
        """Verify radar physical range and sweep angle constants."""
        assert config.RADAR_MAX_RANGE == 15.0
        assert config.RADAR_SWEEP_ANGLE_MIN == 0.0
        assert config.RADAR_SWEEP_ANGLE_MAX == 180.0
        assert config.RADAR_SWEEP_ANGLE_MIN < config.RADAR_SWEEP_ANGLE_MAX

    def test_fft_configuration(self):
        """Verify FFT smoothing and scaling settings."""
        assert isinstance(config.FFT_SMOOTHING_ENABLED, bool)
        assert config.FFT_SMOOTHING_METHOD in ["moving_average", "savgol"]
        assert config.FFT_SAVGOL_WINDOW % 2 == 1  # Window must be odd
        assert config.FFT_SAVGOL_POLYORDER < config.FFT_SAVGOL_WINDOW
        assert config.FFT_IMPEDANCE_OHMS == 50.0
        assert config.FFT_MAGNITUDE_FLOOR_DBM <= -50.0

    def test_target_detection_parameters(self):
        """Verify target detection constants."""
        assert config.TARGET_HISTORY_MAX_SIZE == 50
        assert config.TARGET_FREQ_THRESHOLD_KHZ == 10_000.0
        assert config.FILTERED_EXTREMA_INDEX_THRESHOLD == 2000

    def test_theme_colors(self):
        """Verify theme color dictionary contains standard RGBA keys."""
        required_keys = [
            "background", "card_bg", "grid_lines", "text", 
            "accent", "accent_green", "accent_amber", "target", "plot_bg"
        ]
        for key in required_keys:
            assert key in config.THEME_COLORS
            rgba = config.THEME_COLORS[key]
            assert len(rgba) == 4
            for val in rgba:
                assert 0 <= val <= 255
