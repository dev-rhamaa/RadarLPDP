"""Unit tests for UI callbacks, queue routing, and target history management."""

import queue
import threading
from collections import deque
from unittest.mock import MagicMock, patch
import pytest

from config import TARGET_HISTORY_MAX_SIZE
import app.callbacks as callbacks


@pytest.mark.unit
class TestCallbacksAndQueues:
    """Test suite for callback orchestration and thread messaging queues."""

    def test_target_history_ring_buffer_limit(self):
        """Verify target_history deque strictly respects maximum capacity (50)."""
        test_history = deque(maxlen=TARGET_HISTORY_MAX_SIZE)

        # Append 75 targets
        for i in range(75):
            test_history.append((float(i), float(i * 10)))

        assert len(test_history) == TARGET_HISTORY_MAX_SIZE
        # Oldest targets (0..24) must have been automatically dropped
        assert test_history[0] == (25.0, 250.0)
        assert test_history[-1] == (74.0, 740.0)

    @patch("app.callbacks.dpg")
    @patch("app.callbacks.update_sweep_line")
    @patch("app.callbacks.add_target_to_plot")
    def test_update_ui_from_queues_sweep_and_target(
        self, mock_add_target, mock_update_sweep, mock_dpg, mock_queues
    ):
        """Verify update_ui_from_queues processes sweep and target messages."""
        # 1. Inject sweep angle message
        mock_queues["ppi"].put({"type": "sweep", "angle": 45.0})
        callbacks.update_ui_from_queues(mock_queues)
        assert callbacks.last_known_angle == 45.0
        mock_update_sweep.assert_called_with(45.0)

        # 2. Inject target detection message
        callbacks.target_history.clear()
        mock_queues["ppi"].put({"type": "target", "distance": 6.8})
        callbacks.update_ui_from_queues(mock_queues)
        assert len(callbacks.target_history) == 1
        assert callbacks.target_history[0] == (45.0, 6.8)
        mock_add_target.assert_called_once()

    def test_cleanup_and_exit_sets_stop_event(self):
        """Verify cleanup_and_exit signals threads to terminate."""
        stop_evt = threading.Event()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False

        callbacks.cleanup_and_exit(stop_evt, {"mock_thread": mock_thread})
        assert stop_evt.is_set()
