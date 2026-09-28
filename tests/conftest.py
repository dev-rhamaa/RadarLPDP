"""Pytest configuration and shared fixtures for RadarLPDP testing suite."""

import queue
import threading
from typing import Dict, Tuple
import numpy as np
import pytest

from config import SAMPLE_RATE, BUFFER_SAMPLES, NUM_CHANNELS


@pytest.fixture
def sample_rate() -> int:
    """Default sampling rate (20 MHz)."""
    return SAMPLE_RATE


@pytest.fixture
def buffer_samples() -> int:
    """Default buffer size (20,000 samples)."""
    return BUFFER_SAMPLES


@pytest.fixture
def mock_queues() -> Dict[str, queue.Queue]:
    """Provide a fresh dictionary of thread-safe FIFO queues."""
    return {
        "ppi": queue.Queue(),
        "fft": queue.Queue(),
        "sinewave": queue.Queue(),
        "metrics": queue.Queue(),
    }


@pytest.fixture
def stop_event() -> threading.Event:
    """Provide a thread stop event."""
    return threading.Event()


@pytest.fixture
def synthetic_sine_signal(sample_rate: int, buffer_samples: int):
    """Generate a clean sinusoidal test signal with known frequency and amplitude.
    
    Returns a factory function: make_sine(freq_hz, amplitude_volts, phase_rad, noise_std).
    """
    def _generator(freq_hz: float = 2_500_000.0, 
                   amplitude_volts: float = 0.5, 
                   phase_rad: float = 0.0, 
                   noise_std: float = 0.0) -> np.ndarray:
        t = np.arange(buffer_samples) / sample_rate
        signal = amplitude_volts * np.sin(2.0 * np.pi * freq_hz * t + phase_rad)
        if noise_std > 0.0:
            signal += np.random.normal(0.0, noise_std, size=buffer_samples)
        return signal.astype(np.float32)
    
    return _generator


@pytest.fixture
def synthetic_dual_channel_data(synthetic_sine_signal):
    """Generate synchronized CH0 and CH2 signals with a target beat frequency."""
    # CH0: Target IF return at 3.0 MHz (corresponding to ~4.5 km distance)
    ch0 = synthetic_sine_signal(freq_hz=3_000_000.0, amplitude_volts=0.45, noise_std=0.02)
    # CH2: Reference LO / coupling signal at 3.0 MHz
    ch2 = synthetic_sine_signal(freq_hz=3_000_000.0, amplitude_volts=0.40, phase_rad=0.35, noise_std=0.02)
    return ch0, ch2
