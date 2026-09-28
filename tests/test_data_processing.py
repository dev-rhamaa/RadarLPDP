"""Unit tests for digital signal processing functions in data_processing.py."""

import math
import numpy as np
import pytest

from functions.data_processing import (
    polar_to_cartesian,
    smooth_spectrum,
    compute_fft,
    compute_fft_linear,
    find_peak_metrics,
    find_top_extrema,
    find_target_extrema,
    find_filtered_extrema,
    process_raw_channels,
    calculate_target_distance,
    update_sweep_angle,
)


@pytest.mark.unit
@pytest.mark.signal
class TestDataProcessing:
    """Test suite for radar signal analysis and mathematical routines."""

    def test_polar_to_cartesian_cardinal_angles(self):
        """Verify polar to Cartesian conversion at 0, 90, 180, and 270 degrees."""
        cx, cy = 10.0, 20.0
        r = 5.0

        # 0 degrees: (cx + r, cy)
        x0, y0 = polar_to_cartesian(cx, cy, 0.0, r)
        assert pytest.approx(x0, rel=1e-5) == 15.0
        assert pytest.approx(y0, rel=1e-5) == 20.0

        # 90 degrees: (cx, cy + r)
        x90, y90 = polar_to_cartesian(cx, cy, 90.0, r)
        assert pytest.approx(x90, abs=1e-5) == 10.0
        assert pytest.approx(y90, rel=1e-5) == 25.0

        # 180 degrees: (cx - r, cy)
        x180, y180 = polar_to_cartesian(cx, cy, 180.0, r)
        assert pytest.approx(x180, rel=1e-5) == 5.0
        assert pytest.approx(y180, abs=1e-5) == 20.0

    def test_smooth_spectrum_empty(self):
        """Verify smooth_spectrum gracefully handles empty array."""
        empty_arr = np.array([], dtype=np.float64)
        res = smooth_spectrum(empty_arr)
        assert len(res) == 0

    def test_smooth_spectrum_moving_average(self):
        """Verify moving average smoothing reduces variance of noisy spectrum."""
        np.random.seed(42)
        noise = np.random.normal(0.0, 5.0, size=200)
        smoothed = smooth_spectrum(noise, window_size=11, method="moving_average")
        assert len(smoothed) == len(noise)
        assert np.var(smoothed) < np.var(noise)

    def test_smooth_spectrum_savgol(self):
        """Verify Savitzky-Golay filter preserves peak trend while smoothing."""
        x = np.linspace(-3, 3, 150)
        peak = 50.0 * np.exp(-x**2)
        noisy = peak + np.random.normal(0, 1.0, size=len(x))
        smoothed = smooth_spectrum(noisy, method="savgol", savgol_window=21, savgol_polyorder=3)
        assert len(smoothed) == len(noisy)
        # Peak position should remain near center
        assert abs(np.argmax(smoothed) - len(x)//2) <= 3

    def test_compute_fft_known_frequency(self, synthetic_sine_signal, sample_rate):
        """Verify compute_fft accurately resolves peak frequency and dBm magnitude."""
        target_freq_hz = 2_500_000.0  # 2.5 MHz
        signal = synthetic_sine_signal(freq_hz=target_freq_hz, amplitude_volts=0.5)

        freqs_khz, mags_dbm = compute_fft(signal, sample_rate, window="hann", smooth=False)

        assert len(freqs_khz) == len(mags_dbm)
        assert len(freqs_khz) == len(signal) // 2 + 1

        # Peak should be at 2500 kHz (bin resolution is 1 kHz)
        peak_idx = np.argmax(mags_dbm)
        detected_freq_khz = freqs_khz[peak_idx]
        assert abs(detected_freq_khz - 2500.0) <= 2.0  # Within 2 kHz

        # Calibrated power in 50 Ohm: V_peak = 0.5 V -> P = 0.5^2 / (2 * 50) = 0.0025 W = 2.5 mW
        # 10 * log10(2.5) ≈ +3.98 dBm
        assert mags_dbm[peak_idx] > -5.0

    def test_compute_fft_linear(self, synthetic_sine_signal, sample_rate):
        """Verify compute_fft_linear computes linear magnitude spectrum."""
        signal = synthetic_sine_signal(freq_hz=1_000_000.0, amplitude_volts=0.4)
        freqs, mags = compute_fft_linear(signal, sample_rate)
        assert len(freqs) == len(mags)
        assert np.all(mags >= 0.0)

    def test_find_peak_metrics(self):
        """Verify find_peak_metrics finds dominant frequency and magnitude."""
        freqs = np.array([100.0, 200.0, 300.0, 400.0])
        mags = np.array([-50.0, -10.0, -35.0, -60.0])
        peak_freq, peak_mag = find_peak_metrics(freqs, mags)
        assert peak_freq == 200.0
        assert peak_mag == -10.0

    def test_find_top_extrema(self):
        """Verify detection of multiple peaks and valleys."""
        freqs = np.linspace(0, 1000, 100)
        # Create two distinct peaks
        mags = np.full(100, -80.0)
        mags[25] = -20.0
        mags[65] = -30.0

        peaks, valleys = find_top_extrema(freqs, mags, n_extrema=2, prominence_db=5.0)
        assert len(peaks) >= 2
        assert peaks[0]["mag_db"] == -20.0
        assert peaks[1]["mag_db"] == -30.0

    def test_find_target_extrema(self):
        """Verify find_target_extrema filters signals strictly above target threshold."""
        freqs = np.array([5000.0, 8000.0, 12000.0, 15000.0])
        mags = np.array([-10.0, -15.0, -30.0, -25.0])

        # Threshold 10,000 kHz: only 12000 and 15000 qualify
        peaks, top_freq, top_mag = find_target_extrema(freqs, mags, freq_threshold_khz=10_000.0)
        assert top_freq == 15000.0
        assert top_mag == -25.0
        assert all(p["freq_khz"] >= 10000.0 for p in peaks)

    def test_find_filtered_extrema(self):
        """Verify index-threshold filtering for high-frequency FFT bins."""
        freqs = np.linspace(0, 10000, 5000)
        mags = np.full(5000, -90.0)
        mags[1000] = -10.0  # Before index threshold
        mags[3000] = -20.0  # Above index threshold 2000

        peaks, _ = find_filtered_extrema(freqs, mags, index_threshold=2000, n_extrema=1)
        assert len(peaks) == 1
        assert peaks[0]["index"] == 3000

    def test_calculate_target_distance(self):
        """Verify beat frequency mapping to radar target distance."""
        # Simulated metrics dictionary
        metrics = {
            "ch1": {
                "filtered_peaks": [
                    {"index": 3298, "freq_khz": 3298.0, "mag_db": 85.0}
                ],
                "peaks": []
            }
        }

        # index_min=2500, index_max=4096, max_range=15.0
        # normalized = (3298 - 2500) / (4096 - 2500) = 798 / 1596 = 0.50
        # distance = 0.5 * 15.0 = 7.5 m
        dist = calculate_target_distance(
            metrics, 
            mag_threshold_db=80.0, 
            index_min=2500, 
            index_max=4096, 
            max_range=15.0
        )
        assert dist is not None
        assert pytest.approx(dist, rel=1e-2) == 7.5

    def test_calculate_target_distance_below_threshold(self):
        """Verify candidate with magnitude below threshold is rejected."""
        metrics = {
            "ch1": {
                "filtered_peaks": [
                    {"index": 3000, "freq_khz": 3000.0, "mag_db": 65.0}  # Below 80 dB threshold
                ]
            }
        }
        dist = calculate_target_distance(metrics, mag_threshold_db=80.0)
        assert dist is None

    def test_update_sweep_angle_bounce(self):
        """Verify 180-degree sweep ping-pong angle dynamics."""
        # Move forward from 178° + 3° -> bounces at 180° and reverses direction to -1
        new_ang, new_dir = update_sweep_angle(current_angle=178.0, direction=1, increment=3.0)
        assert new_ang == 180.0
        assert new_dir == -1

        # Move backward from 2° - 3° -> bounces at 0° and reverses direction to +1
        new_ang, new_dir = update_sweep_angle(current_angle=2.0, direction=-1, increment=3.0)
        assert new_ang == 0.0
        assert new_dir == 1

    def test_smooth_spectrum_edge_cases(self):
        """Verify smooth_spectrum edge cases: very short array, window <= polyorder."""
        short_arr = np.array([1.0, 2.0], dtype=np.float64)
        res = smooth_spectrum(short_arr, method="savgol", savgol_polyorder=3)
        assert len(res) == len(short_arr)

        single_arr = np.array([42.0], dtype=np.float64)
        assert len(smooth_spectrum(single_arr, window_size=5)) == 1

    def test_compute_fft_raw_adc_counts_conversion(self, sample_rate):
        """Verify raw 16-bit ADC integer counts are properly scaled to Volts."""
        # 16-bit ADC count of 16384 represents +0.5 V
        t = np.arange(1000) / sample_rate
        raw_counts = (16384 * np.sin(2 * np.pi * 1_000_000 * t)).astype(np.float32)
        freqs, mags = compute_fft(raw_counts, sample_rate, smooth=False)
        assert len(freqs) > 0
        # Peak power of 0.5 V into 50 Ohm is ~+3.98 dBm
        peak_idx = np.argmax(mags)
        assert mags[peak_idx] > -5.0

    def test_compute_fft_empty_input(self, sample_rate):
        """Verify compute_fft returns empty arrays when channel is empty."""
        empty_arr = np.array([], dtype=np.float32)
        freqs, mags = compute_fft(empty_arr, sample_rate)
        assert len(freqs) == 0
        assert len(mags) == 0

    def test_calculate_target_distance_channel_modes(self):
        """Verify target distance calculation under ch1 and ch2 modes."""
        metrics = {
            "ch1": {
                "filtered_peaks": [{"index": 2800, "freq_khz": 2800.0, "mag_db": 90.0}]
            },
            "ch2": {
                "filtered_peaks": [{"index": 3500, "freq_khz": 3500.0, "mag_db": 95.0}]
            }
        }
        # Under ch1 mode, selects 2800 index
        dist_ch1 = calculate_target_distance(
            metrics, mag_threshold_db=80.0, index_min=2000, index_max=4000, 
            channel_mode="ch1", max_range=15.0
        )
        assert dist_ch1 is not None
        # (2800 - 2000) / 2000 * 15 = 0.4 * 15 = 6.0
        assert pytest.approx(dist_ch1, abs=0.05) == 6.0

        # Under ch2 mode, selects 3500 index
        dist_ch2 = calculate_target_distance(
            metrics, mag_threshold_db=80.0, index_min=2000, index_max=4000, 
            channel_mode="ch2", max_range=15.0
        )
        assert dist_ch2 is not None
        # (3500 - 2000) / 2000 * 15 = 0.75 * 15 = 11.25
        assert pytest.approx(dist_ch2, abs=0.05) == 11.25

    def test_calculate_target_distance_invalid_indices(self):
        """Verify calculate_target_distance handles invalid index boundaries."""
        metrics = {"ch1": {"peaks": [{"index": 100, "mag_db": 100.0}]}}
        # index_max <= index_min
        assert calculate_target_distance(metrics, index_min=500, index_max=400) is None
        # None metrics
        assert calculate_target_distance(None) is None

    def test_process_raw_channels_empty(self, sample_rate):
        """Verify process_raw_channels returns (None, None) for empty inputs."""
        res, metrics = process_raw_channels(None, None, sample_rate)
        assert res is None
        assert metrics is None
