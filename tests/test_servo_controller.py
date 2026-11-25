# -*- coding: utf-8 -*-
"""Tests for the centre-relative servo mapping and the worker's start-up centring logic."""

import queue
import threading
import time

import pytest

import app.servo_controller as sc


class FakeDriver:
    """Minimal KYDAS4801A stand-in: answers ED 08 queries and chases the last E0 01 target."""

    def __init__(self, start_position: int, step: int = 40_000):
        self.position = start_position
        self.target = start_position
        self.step = step
        self.sent_targets = []
        self._rx = bytearray()

    # --- serial.Serial API used by servo_controller ---
    def __call__(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def reset_input_buffer(self):
        self._rx.clear()

    def flush(self):
        pass

    def write(self, data: bytes):
        data = bytes(data)
        if data[:2] == b"\xED\x08":
            # driver moves a bit towards the target on every poll, then reports
            delta = self.target - self.position
            self.position += max(-self.step, min(self.step, delta))
            self._rx.extend(b"\xED\x08" + int(self.position).to_bytes(4, "big", signed=True))
        elif data[:4] == b"\xE0\x01\x00\x00":
            self.target = int.from_bytes(data[4:8], "big", signed=True)
            self.sent_targets.append(self.target)

    def read(self, n: int = 1) -> bytes:
        out = bytes(self._rx[:n])
        del self._rx[:n]
        return out


# ------------------------------------------------------------------ pure mapping

def test_mapping_is_relative_to_center():
    cpd = sc.COUNTS_PER_DEG
    for center in (-10_000, 0, 123_456):
        assert sc.degrees_to_counts(90.0, center) == center
        assert sc.degrees_to_counts(30.0, center) == round(center + 60 * cpd)
        assert sc.degrees_to_counts(150.0, center) == round(center - 60 * cpd)
        assert sc.counts_to_degrees(center, center) == pytest.approx(90.0)


def test_mapping_roundtrip_and_direction():
    center = 777
    for deg in (30.0, 45.5, 90.0, 120.25, 150.0):
        counts = sc.degrees_to_counts(deg, center)
        assert sc.counts_to_degrees(counts, center) == pytest.approx(deg, abs=1e-3)
    # positif = kiri (sudut mengecil), negatif = kanan
    assert sc.degrees_to_counts(30.0, center) > center > sc.degrees_to_counts(150.0, center)


def test_mapping_matches_previous_calibration():
    """Dengan titik tengah lama (-10.000) hasilnya sama dengan kalibrasi hard-coded sebelumnya."""
    assert sc.degrees_to_counts(30.0, -10_000) == 120_000
    assert sc.degrees_to_counts(150.0, -10_000) == -140_000


# ------------------------------------------------------------------ worker

def _run_worker(monkeypatch, tmp_path, start_position, seconds, state_updates):
    monkeypatch.setattr(sc, "STATE_FILE", str(tmp_path / "servo_state.json"))
    monkeypatch.setattr(sc, "POLL_INTERVAL", 0.001)
    driver = FakeDriver(start_position)
    monkeypatch.setattr(sc.serial, "Serial", driver)

    ppi_queue: "queue.Queue" = queue.Queue()
    stop = threading.Event()
    worker = threading.Thread(
        target=sc.run_servo_angle_worker, args=(ppi_queue, stop, "FAKE"), daemon=True
    )
    worker.start()

    t_end = time.time() + seconds
    for delay, fn in state_updates:
        time.sleep(delay)
        fn()
    time.sleep(max(0.0, t_end - time.time()))
    stop.set()
    worker.join(timeout=5.0)
    assert not worker.is_alive()

    angles = []
    while not ppi_queue.empty():
        angles.append(ppi_queue.get_nowait()["angle"])
    return driver, angles


@pytest.mark.parametrize("start_position", [0, 5_000, -10_000, 987_654])
def test_worker_takes_center_from_motor_position(monkeypatch, tmp_path, start_position):
    """Titik tengah = posisi motor saat start, berapa pun nilai counternya."""
    driver, angles = _run_worker(
        monkeypatch, tmp_path, start_position, seconds=2.0,
        state_updates=[(0.3, lambda: sc.set_servo_running(True))],
    )
    cpd = sc.COUNTS_PER_DEG

    # sudut PPI pertama = 90 deg walau counter awal bukan -10.000
    assert angles[0] == pytest.approx(90.0)

    # sapuan: target pertama ke 150 deg (kanan), lalu 30 deg (kiri), relatif ke posisi awal
    right = round(start_position - 60 * cpd)
    left = round(start_position + 60 * cpd)
    assert right in driver.sent_targets
    assert left in driver.sent_targets
    assert driver.sent_targets.index(right) < driver.sent_targets.index(left)

    # seluruh sudut yang dilaporkan berada di sektor 30..150 deg
    assert min(angles) == pytest.approx(30.0, abs=0.5)
    assert max(angles) == pytest.approx(150.0, abs=0.5)


def test_worker_returns_to_center_on_stop(monkeypatch, tmp_path):
    start = 5_000

    def start_motor():
        sc.set_servo_running(True)

    def stop_motor():
        sc.set_servo_running(False)

    driver, angles = _run_worker(
        monkeypatch, tmp_path, start, seconds=2.5,
        state_updates=[(0.3, start_motor), (1.0, stop_motor)],
    )
    # setelah STOP motor kembali ke titik tengah (counter awal), bukan ke konstanta tetap
    assert driver.target == start
    assert driver.position == start
    assert angles[-1] == pytest.approx(90.0, abs=0.1)


def test_manual_target_is_relative_to_center(monkeypatch, tmp_path):
    start = -250
    driver, angles = _run_worker(
        monkeypatch, tmp_path, start, seconds=1.5,
        state_updates=[
            (0.3, lambda: sc.set_servo_target_degrees(60.0)),
            (0.0, lambda: sc.set_servo_running(True)),
        ],
    )
    # (saat worker berhenti ia selalu menutup dengan kembali ke tengah, jadi cek target yang dikirim)
    assert sc.degrees_to_counts(60.0, start) in driver.sent_targets
    assert min(angles) == pytest.approx(60.0, abs=0.1)


def test_state_file_has_no_absolute_counts(monkeypatch, tmp_path):
    monkeypatch.setattr(sc, "STATE_FILE", str(tmp_path / "servo_state.json"))
    sc.reset_servo_state_on_startup()
    state = sc.get_servo_state()
    assert "target_counts" not in state and "active_target" not in state
    assert state["target_deg"] == 90.0 and state["running"] is False
