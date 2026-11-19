"""KYDAS4801A Servo Motor Position Controller & PPI Beam Sweep Worker.

Provides both Auto Scan and Manual Target positioning with state persistence in servo_state.json.
Calibrated mapping: 0 deg = +140,000 counts, 90 deg = +10,000 counts, 180 deg = -120,000 counts.
Initial home position is fixed at 90 deg whether motor is running or stopped.
"""

import json
import math
import os
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import serial

from config import (
    SERIAL_PORT as DEFAULT_COM_PORT,
    BAUD_RATE as DEFAULT_BAUD_RATE,
    PROJECT_ROOT,
    SERVO_CENTER_POSITION,
    SERVO_TARGET_0_DEG,
    SERVO_TARGET_180_DEG,
    SERVO_POSITION_TOLERANCE,
    SERVO_POLL_INTERVAL,
)

# --- Hardware Constants (KYDAS4801A) ---
# Kalibrasi: 0 deg = +140,000 counts, 90 deg = +10,000 counts, 180 deg = -120,000 counts
TARGET_0_DEG = SERVO_TARGET_0_DEG        # +140_000 counts (0 degrees)
TARGET_90_DEG = SERVO_CENTER_POSITION    # +10_000 counts (90 degrees home / awal)
TARGET_180_DEG = SERVO_TARGET_180_DEG    # -120_000 counts (180 degrees)
CENTER_POSITION = TARGET_90_DEG          # +10_000 counts
MIN_POSITION = min(TARGET_0_DEG, TARGET_180_DEG)  # -120_000 counts
MAX_POSITION = max(TARGET_0_DEG, TARGET_180_DEG)  # +140_000 counts
HALF_SPAN_COUNTS = (MAX_POSITION - MIN_POSITION) // 2  # 130_000 counts

POSITIVE_TARGET = max(TARGET_0_DEG, TARGET_180_DEG)  # +140_000 counts
NEGATIVE_TARGET = min(TARGET_0_DEG, TARGET_180_DEG)  # -120_000 counts
POSITION_TOLERANCE = SERVO_POSITION_TOLERANCE        # 150 counts (~0.104 deg)

POLL_INTERVAL = SERVO_POLL_INTERVAL      # ~12.5 Hz angle refresh rate
START_DELAY = 1.0                        # Hold initial position on startup
RESPONSE_TIMEOUT = 1.0                   # Response deadline for query
MOVE_TIMEOUT = 120.0                     # Max time allowed per single sweep stroke

STATE_FILE = str(PROJECT_ROOT / "servo_state.json")

QUERY_POSITION = bytes.fromhex("ED 08 00 00 00 00 00 00")
DISABLE_PACKET = bytes.fromhex("E0 00 00 00 00 00 00 00")


def counts_to_degrees(position: int) -> float:
    """Map encoder counts to angles in degrees (0 to 180 deg).

    +140,000 counts -> 0 degrees
     +10,000 counts -> 90 degrees
    -120,000 counts -> 180 degrees
    """
    pos = float(position)
    # Tentukan apakah posisi berada di segmen 0..90 derajat (antara TARGET_0_DEG dan CENTER_POSITION)
    is_in_first_half = (pos >= CENTER_POSITION) if TARGET_0_DEG >= CENTER_POSITION else (pos <= CENTER_POSITION)
    if is_in_first_half:
        if CENTER_POSITION == TARGET_0_DEG:
            return 90.0
        deg = 0.0 + (pos - TARGET_0_DEG) * 90.0 / (CENTER_POSITION - TARGET_0_DEG)
    else:
        if TARGET_180_DEG == CENTER_POSITION:
            return 90.0
        deg = 90.0 + (pos - CENTER_POSITION) * 90.0 / (TARGET_180_DEG - CENTER_POSITION)
    return max(0.0, min(180.0, deg))


def degrees_to_counts(degrees: float) -> int:
    """Map angle in degrees back to target counts (+140k at 0 deg, +10k at 90 deg, -120k at 180 deg)."""
    deg = max(0.0, min(180.0, float(degrees)))
    if deg <= 90.0:
        counts = TARGET_0_DEG + (deg / 90.0) * (CENTER_POSITION - TARGET_0_DEG)
    else:
        counts = CENTER_POSITION + ((deg - 90.0) / 90.0) * (TARGET_180_DEG - CENTER_POSITION)
    return int(round(counts))


def disable_servo(ser: serial.Serial) -> bool:
    """Send emergency disable command to servo driver."""
    try:
        ser.write(DISABLE_PACKET)
        ser.flush()
        print("[servo] Perintah DISABLE terkirim ke driver KYDAS4801A.")
        return True
    except Exception as err:
        print(f"[servo] Gagal mengirim DISABLE: {err}")
        return False


def send_position(ser: serial.Serial, position: int) -> bool:
    """Send absolute 32-bit signed big-endian position target."""
    try:
        pos_int = int(position)
        packet = bytes.fromhex("E0 01 00 00") + pos_int.to_bytes(4, byteorder="big", signed=True)
        ser.write(packet)
        ser.flush()
        return True
    except Exception as err:
        print(f"[servo] Gagal mengirim target posisi: {err}")
        return False


def read_position(
    ser: serial.Serial,
    timeout: float = RESPONSE_TIMEOUT,
    stop_event: Optional[threading.Event] = None
) -> Optional[int]:
    """Query cumulative position from driver response (ED 08 + 4 bytes)."""
    if stop_event and stop_event.is_set():
        return None

    try:
        ser.reset_input_buffer()
        ser.write(QUERY_POSITION)
        ser.flush()

        buffer = bytearray()
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if stop_event and stop_event.is_set():
                return None

            data = ser.read(1)
            if not data:
                continue

            buffer.extend(data)
            header_idx = buffer.find(b"\xED\x08")
            if header_idx >= 0 and len(buffer) >= header_idx + 6:
                frame = buffer[header_idx:header_idx + 6]
                pos_bytes = frame[2:6]
                return int.from_bytes(pos_bytes, byteorder="big", signed=True)

            if len(buffer) > 64:
                del buffer[:-5]

    except Exception:
        pass

    return None


def get_servo_state() -> Dict[str, Any]:
    """Read current desired state from state file."""
    default_state = {
        "running": False,
        "mode": "scan",
        "target_deg": 90.0,
        "target_counts": CENTER_POSITION,
        "active_target": TARGET_180_DEG,
        "updated_at": time.time(),
    }
    if not os.path.exists(STATE_FILE):
        return default_state

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {**default_state, **data}
    except Exception:
        pass
    return default_state


def set_servo_running(running: bool) -> None:
    """Start or stop servo motor operation."""
    state = get_servo_state()
    state["running"] = bool(running)
    if not running:
        # Saat motor dimatikan (STOP), reset target ke posisi awal 90 derajat
        state["target_deg"] = 90.0
        state["target_counts"] = CENTER_POSITION
    state["updated_at"] = time.time()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
        print(f"[servo] State updated: {'MULAI (RUNNING)' if running else 'STOP (STANDBY - Posisi 90°)'}")
    except Exception as e:
        print(f"[servo] Failed to write servo state: {e}")


def is_servo_running() -> bool:
    """Check whether servo is currently running."""
    return bool(get_servo_state().get("running", False))


def reset_servo_state_on_startup() -> None:
    """Ensure servo always starts at 90 degrees and in STOPPED/STANDBY mode on application launch."""
    state = {
        "running": False,
        "mode": "scan",
        "target_deg": 90.0,
        "target_counts": CENTER_POSITION,
        "active_target": TARGET_180_DEG,
        "updated_at": time.time(),
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def set_servo_target_degrees(degrees: float) -> None:
    """Set manual target position in degrees and switch to manual mode."""
    target_counts = degrees_to_counts(degrees)
    state = get_servo_state()
    state["mode"] = "manual"
    state["target_deg"] = float(degrees)
    state["target_counts"] = int(target_counts)
    state["updated_at"] = time.time()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
        print(f"[servo] Manual target updated: {degrees:.1f}° ({target_counts} counts)")
    except Exception as e:
        print(f"[servo] Failed to write servo state: {e}")


def set_servo_mode(mode: str) -> None:
    """Switch mode between 'scan' and 'manual'."""
    state = get_servo_state()
    state["mode"] = "scan" if mode.lower() == "scan" else "manual"
    state["updated_at"] = time.time()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
        print(f"[servo] Mode changed to: {state['mode']}")
    except Exception as e:
        print(f"[servo] Failed to update servo mode: {e}")


def run_servo_angle_worker(
    ppi_queue: queue.Queue,
    stop_event: threading.Event,
    port: Optional[str] = None,
    baudrate: int = DEFAULT_BAUD_RATE,
) -> None:
    """Worker thread controlling servo motor and feeding azimuth angles to PPI."""
    target_port = port or DEFAULT_COM_PORT
    sim_angle = 90.0
    sim_dir = 1.0
    sim_speed = 25.0
    last_sim_time = time.time()
    last_port_retry = 0.0

    # Pastikan state awal selalu pada posisi 90 derajat dalam status STOPPED
    reset_servo_state_on_startup()

    print(f"[servo] Menginisialisasi servo controller pada port {target_port} ({baudrate} baud)...")
    print("[servo] Status awal: MOTOR STOPPED - Posisi awal 90°.")

    while not stop_event.is_set():
        try:
            with serial.Serial(
                port=target_port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            ) as ser:
                print(f"[servo] Berhasil terhubung ke driver servo KYDAS4801A pada {target_port}!")
                time.sleep(0.3)

                current_position = read_position(ser, timeout=1.5, stop_event=stop_event)
                if current_position is None:
                    time.sleep(1.0)
                    continue

                # Posisikan motor ke posisi awal 90 derajat saat terhubung
                print(f"[servo] Mengarahkan motor ke posisi awal 90° ({CENTER_POSITION} counts)...")
                send_position(ser, CENTER_POSITION)
                last_sent_target = CENTER_POSITION
                last_command_time = time.monotonic()

                init_angle = counts_to_degrees(current_position)
                ppi_queue.put({"type": "sweep", "angle": init_angle})

                scan_target = TARGET_180_DEG
                was_running = False
                last_active_mode = None

                while not stop_event.is_set():
                    state = get_servo_state()
                    is_running = state.get("running", False)
                    active_mode = state.get("mode", "scan")

                    # KONDISI MOTOR MATI (STOP / STANDBY)
                    if not is_running:
                        desired_target = CENTER_POSITION
                        now = time.monotonic()
                        if last_sent_target != desired_target or (now - last_command_time > 2.0):
                            send_position(ser, desired_target)
                            last_sent_target = desired_target
                            last_command_time = now

                        if was_running:
                            was_running = False
                            last_active_mode = None
                            print("[servo] Motor STOP -> Kembali ke posisi awal 90°.")

                        # Monitoring sudut riil motor untuk pembaruan garis sweep PPI
                        pos = read_position(ser, timeout=0.08, stop_event=stop_event)
                        if pos is not None:
                            current_position = pos
                            deg = counts_to_degrees(current_position)
                            ppi_queue.put({"type": "sweep", "angle": deg})

                        time.sleep(POLL_INTERVAL)
                        continue

                    # KONDISI MOTOR NYALA (RUNNING)
                    if not was_running:
                        was_running = True
                        print(f"[servo] Motor NYALA (MULAI) dari posisi awal 90° - Mode: {active_mode}")
                        last_sent_target = None
                        if active_mode == "scan":
                            scan_target = TARGET_180_DEG if counts_to_degrees(current_position) <= 90.0 else TARGET_0_DEG
                        last_active_mode = active_mode

                    # Deteksi pergantian mode saat motor sedang berjalan
                    if active_mode != last_active_mode:
                        print(f"[servo] Mode aktif berganti: {last_active_mode} -> {active_mode}")
                        last_sent_target = None
                        if active_mode == "scan":
                            scan_target = TARGET_180_DEG if counts_to_degrees(current_position) <= 90.0 else TARGET_0_DEG
                        last_active_mode = active_mode

                    if active_mode == "manual":
                        desired_target = int(state.get("target_counts", CENTER_POSITION))
                    else:
                        desired_target = scan_target

                    # Kirim perintah target jika berubah atau periodik
                    now = time.monotonic()
                    if desired_target != last_sent_target or (now - last_command_time > 2.0):
                        send_position(ser, desired_target)
                        last_sent_target = desired_target
                        last_command_time = now

                    pos = read_position(ser, timeout=0.08, stop_event=stop_event)
                    if pos is not None:
                        current_position = pos
                        deg = counts_to_degrees(current_position)
                        ppi_queue.put({"type": "sweep", "angle": deg})

                        if active_mode == "scan":
                            reached = False
                            if scan_target == TARGET_180_DEG:
                                if TARGET_180_DEG >= TARGET_0_DEG:
                                    reached = current_position >= (TARGET_180_DEG - POSITION_TOLERANCE)
                                else:
                                    reached = current_position <= (TARGET_180_DEG + POSITION_TOLERANCE)
                            elif scan_target == TARGET_0_DEG:
                                if TARGET_0_DEG <= TARGET_180_DEG:
                                    reached = current_position <= (TARGET_0_DEG + POSITION_TOLERANCE)
                                else:
                                    reached = current_position >= (TARGET_0_DEG - POSITION_TOLERANCE)
                            if abs(scan_target - current_position) <= POSITION_TOLERANCE:
                                reached = True

                            if reached:
                                scan_target = TARGET_0_DEG if scan_target == TARGET_180_DEG else TARGET_180_DEG
                                last_sent_target = None
                                time.sleep(0.08)

                    time.sleep(POLL_INTERVAL)

                send_position(ser, CENTER_POSITION)
                time.sleep(0.2)
                disable_servo(ser)
                break

        except (serial.SerialException, OSError) as e:
            now = time.time()
            if now - last_port_retry > 5.0:
                print(f"[servo] Port {target_port} tidak merespons ({e}). Menjalankan simulasi azimuth...")
                last_port_retry = now

            state = get_servo_state()
            is_running = state.get("running", False)
            active_mode = state.get("mode", "scan")

            now_t = time.time()
            dt = now_t - last_sim_time
            last_sim_time = now_t

            # Mode simulasi
            if is_running:
                if active_mode == "manual":
                    tgt = float(state.get("target_deg", 90.0))
                    diff = tgt - sim_angle
                    step = math.copysign(min(abs(diff), sim_speed * dt), diff)
                    sim_angle += step
                else:
                    sim_angle += sim_dir * sim_speed * dt
                    if sim_angle >= 180.0:
                        sim_angle = 180.0
                        sim_dir = -1.0
                    elif sim_angle <= 0.0:
                        sim_angle = 0.0
                        sim_dir = 1.0
            else:
                # Motor MATI: kembali dan bertahan di posisi 90 derajat
                diff = 90.0 - sim_angle
                if abs(diff) > 0.1:
                    step = math.copysign(min(abs(diff), sim_speed * dt * 2.0), diff)
                    sim_angle += step
                else:
                    sim_angle = 90.0

            try:
                ppi_queue.put_nowait({"type": "sweep", "angle": sim_angle})
            except queue.Full:
                pass

            stop_event.wait(0.04)

    print("[servo] Worker servo controller selesai.")
