"""Unit tests for C acquisition engine, driver bindings, and hardware error handling."""

import queue
import threading
import pytest
from unittest.mock import MagicMock, patch

from app.c_acquisition import DaskDriver, NativeCAcquisitionEngine


@pytest.mark.unit
@pytest.mark.daq
class TestCAcquisition:
    """Test suite for native C driver wrapper and DAQ engine error handling."""

    def test_dask_driver_initialization(self):
        """Verify DaskDriver initializes and is_available is a boolean."""
        driver = DaskDriver()
        assert isinstance(driver.is_available, bool)

    def test_engine_initialization_defaults(self):
        """Verify NativeCAcquisitionEngine correctly sets default attributes."""
        callback_mock = MagicMock()
        engine = NativeCAcquisitionEngine(
            sample_rate_hz=20_000_000,
            buffer_samples=20_000,
            channels=(0, 2),
            write_live_bin=False,
            batch_log_enabled=False,
            on_event_received=callback_mock
        )

        assert engine.sample_rate_hz == 20_000_000
        assert engine.buffer_samples == 20_000
        assert engine.channels == (0, 2)
        assert engine.channel_count == 2
        assert engine.event_count == 0
        assert engine.status == "INITIALIZED"
        assert engine.last_error is None
        assert engine.is_running is False
        assert engine.on_event_received is callback_mock

    def test_hardware_unavailable_on_development_environment(self):
        """Verify is_hardware_available detects absence of physical PCIe card."""
        engine = NativeCAcquisitionEngine()
        # On developer PC / laptop without ADLink PCI-9846H PCIe card, must be False
        assert engine.is_hardware_available() is False

    def test_check_hardware_or_raise_fails_when_no_card(self):
        """Verify check_hardware_or_raise explicitly raises RuntimeError when hardware is absent."""
        engine = NativeCAcquisitionEngine()
        with pytest.raises(RuntimeError) as exc_info:
            engine.check_hardware_or_raise()

        assert "tidak terdeteksi" in str(exc_info.value)
        assert engine.status in ["HARDWARE_NOT_FOUND", "DRIVER_NOT_FOUND"]
        assert engine.last_error is not None

    def test_engine_start_strict_mode_raises_error(self):
        """Verify start(raise_if_no_hardware=True) fails fast when hardware is missing."""
        engine = NativeCAcquisitionEngine()
        with pytest.raises(RuntimeError) as exc_info:
            engine.start(raise_if_no_hardware=True)

        assert "tidak terdeteksi" in str(exc_info.value)

    def test_acquisition_loop_records_hardware_not_found(self):
        """Verify background worker marks status as HARDWARE_NOT_FOUND when card is missing."""
        engine = NativeCAcquisitionEngine(write_live_bin=False, batch_log_enabled=False)
        # Start normal background worker
        engine.start(raise_if_no_hardware=False)
        # Wait briefly for thread to attempt registration and enter standby
        if engine._thread:
            engine._thread.join(timeout=1.0)

        assert engine.status == "HARDWARE_NOT_FOUND"
        assert "Gagal registrasi" in engine.last_error
        assert engine.is_running is False
        engine.stop()

    def test_engine_start_stop_simulation_fallback(self):
        """Verify engine start and stop behavior with mock driver in software fallback."""
        engine = NativeCAcquisitionEngine(write_live_bin=False, batch_log_enabled=False)
        engine.driver.is_available = False

        engine.start()
        engine.stop()
        assert engine.is_running is False
