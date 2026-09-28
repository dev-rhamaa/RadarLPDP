"""End-to-end integration tests for radar signal acquisition and processing pipeline."""

import numpy as np
import pytest

from functions.data_processing import (
    process_raw_channels,
    calculate_target_distance,
    polar_to_cartesian,
)


@pytest.mark.integration
class TestIntegrationPipeline:
    """Integration test suite verifying full data flow from ADC frame to target distance."""

    def test_end_to_end_radar_detection_pipeline(self, sample_rate, buffer_samples):
        """Verify simulated radar echo progresses from raw samples to verified distance."""
        # 1. Synthesize radar return with known parameters:
        # Sampling: 20 MS/s, 20,000 samples (1 ms)
        t = np.arange(buffer_samples) / sample_rate
        f_target = 3_500_000.0  # 3.5 MHz

        # Target peak index: 3500 (since 20,000 samples @ 20 MHz gives 1 kHz per bin)
        target_signal = 0.5 * np.sin(2 * np.pi * f_target * t)
        noise = np.random.normal(0, 0.05, size=buffer_samples)
        ch0_raw = (target_signal + noise).astype(np.float32)
        ch2_raw = (0.4 * np.sin(2 * np.pi * f_target * t + 0.2) + noise).astype(np.float32)

        # 2. Process raw channels through DSP core
        fft_result, metrics = process_raw_channels(ch0_raw, ch2_raw, sample_rate)

        assert fft_result is not None
        assert fft_result["status"] == "done"
        assert len(fft_result["freqs_ch1"]) == buffer_samples // 2 + 1
        assert len(fft_result["mag_ch1"]) == buffer_samples // 2 + 1
        assert metrics is not None

        # 3. Check that dominant peak in metrics is near 3.5 MHz (3500 kHz)
        peak_freq = metrics["ch1"]["peak_freq"]
        assert abs(peak_freq - 3500.0) <= 5.0

        # 4. Inject verified target peak into metrics to test distance calculation
        # With index_min=2500, index_max=4500, max_range=15.0:
        # Expected distance = ((3500 - 2500) / (4500 - 2500)) * 15.0 = (1000 / 2000) * 15.0 = 7.5 m
        metrics_with_peak = {
            "ch1": {
                "filtered_peaks": [
                    {"index": 3500, "freq_khz": 3500.0, "mag_db": -10.0}
                ]
            }
        }
        distance = calculate_target_distance(
            metrics_with_peak,
            mag_threshold_db=-50.0,
            index_min=2500,
            index_max=4500,
            max_range=15.0
        )

        assert distance is not None
        assert pytest.approx(distance, abs=0.1) == 7.5

        # 5. Verify polar to Cartesian mapping for PPI radar plotting
        angle_deg = 60.0
        x_target, y_target = polar_to_cartesian(0.0, 0.0, angle_deg, distance)
        expected_x = distance * np.cos(np.radians(angle_deg))
        expected_y = distance * np.sin(np.radians(angle_deg))
        assert pytest.approx(x_target, rel=1e-3) == expected_x
        assert pytest.approx(y_target, rel=1e-3) == expected_y
