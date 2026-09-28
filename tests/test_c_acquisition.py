"""Unit tests for C acquisition engine and driver bindings in app/c_acquisition.py."""

import queue
import threading
import pytest
from unittest.mock import MagicMock, patch

from app.c_acquisition import DaskDriver, NativeCAcquisitionEngine


@pytest.mark.unit
@pytest.mark.daq
class TestCAcquisition:
    """Test suite for native C driver wrapper and DAQ engine."""

    def test_dask_driver_initialization(self):
        """Verify DaskDriver initializes without crashing, even if hardware DLL is absent."""
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
        assert engine.on_event_received is callback_mock

    def test_engine_start_stop_simulation_fallback(self):
        """Verify engine start and stop behavior with mock driver in software fallback."""
        engine = NativeCAcquisitionEngine(
            write_live_bin=False,
            batch_log_enabled=False
        )

        # Mock driver as unavailable to test fallback / graceful exit
        engine.driver.is_available = False

        engine.start()
        engine.stop()
        # When driver is not available, start() returns False or stops thread safely
        assert engine._thread is None or not engine._thread.is_alive()
