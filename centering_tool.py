# -*- coding: utf-8 -*-
"""Mini app centering motor servo KYDAS4801A.

Dua tombol (KIRI / KANAN) untuk menggeser motor sedikit demi sedikit sampai antena
menghadap tengah (90 deg). Setelah pas, tutup tool ini lalu jalankan ``main.py``:
radar otomatis memakai posisi motor saat itu sebagai titik tengah (tidak ada nilai tengah
yang perlu disalin ke ``config.py``). "Tandai TENGAH" hanya memindahkan jendela batas
1 putaran di tool ini ke posisi sekarang.

Batas gerak: total 1 putaran antena = 10.485.760 counts (+-5.242.880 dari titik tengah).

Skala counts (dari datasheet ENCODER.pdf + gearbox 80:1):
    encoder absolut 17-bit            = 131.072 counts / putaran motor
    gearbox 80:1                      -> 10.485.760 counts / putaran antena
    1 derajat antena                  = 29.127,11 counts

Arah: counts POSITIF = KIRI, counts NEGATIF = KANAN (sama dengan kalibrasi di config.py).

PENTING: port serial tidak bisa dipakai dua program sekaligus. Tutup ``main.py``
sebelum menjalankan tool ini.

Jalankan:  python centering_tool.py
"""

import queue
import threading
import time
from typing import Any, Dict, Optional

import dearpygui.dearpygui as dpg
import serial

from app.servo_controller import disable_servo, read_position, send_position
from config import BAUD_RATE, SERIAL_PORT

# --- Skala dari datasheet (ENCODER.pdf: 17-bit single-turn + gearbox 80:1) ---
ENCODER_BITS = 17
GEAR_RATIO = 80
COUNTS_PER_MOTOR_REV = 1 << ENCODER_BITS                        # 131.072
COUNTS_PER_ANTENNA_REV = COUNTS_PER_MOTOR_REV * GEAR_RATIO      # 10.485.760
COUNTS_PER_DEG = COUNTS_PER_ANTENNA_REV / 360.0                 # ~29.127,11

MAX_TRAVEL_COUNTS = COUNTS_PER_ANTENNA_REV                      # batas total 1 putaran
HALF_TRAVEL_COUNTS = MAX_TRAVEL_COUNTS // 2                     # +-5.242.880 dari titik tengah

STEP_OPTIONS_DEG = ["0.1", "0.5", "1", "5"]
DEFAULT_STEP_DEG = "1"

POLL_TIMEOUT = 0.08


def deg_to_counts(degrees: float) -> int:
    """Konversi derajat antena ke counts (dibulatkan)."""
    return int(round(degrees * COUNTS_PER_DEG))


def counts_to_deg(counts: float) -> float:
    """Konversi counts ke derajat antena."""
    return counts / COUNTS_PER_DEG


def clamp_target(target: int, anchor: int) -> int:
    """Batasi target ke jendela 1 putaran (anchor +- 5.242.880 counts)."""
    return max(anchor - HALF_TRAVEL_COUNTS, min(anchor + HALF_TRAVEL_COUNTS, int(target)))


# --- State bersama antara worker thread dan UI ---
_lock = threading.Lock()
_state: Dict[str, Any] = {
    "connected": False,
    "status": "Belum terhubung",
    "position": None,     # counts, hasil baca driver
    "target": None,       # counts, target terakhir yang dikirim
    "anchor": None,       # titik tengah jendela 1 putaran
    "msg": "",
}
_cmds: "queue.Queue[tuple]" = queue.Queue()
_stop_event = threading.Event()
_worker: Optional[threading.Thread] = None


def _set(**kwargs: Any) -> None:
    with _lock:
        _state.update(kwargs)


def _snapshot() -> Dict[str, Any]:
    with _lock:
        return dict(_state)


def _worker_loop(port: str, stop_event: threading.Event) -> None:
    """Satu-satunya pemilik koneksi serial: kirim perintah, baca posisi terus-menerus."""
    try:
        with serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        ) as ser:
            time.sleep(0.3)
            pos = None
            for _ in range(3):
                pos = read_position(ser, timeout=1.0, stop_event=stop_event)
                if pos is not None:
                    break
            if pos is None:
                _set(connected=False, status=f"{port}: driver tidak merespons")
                return

            _set(
                connected=True,
                status=f"Terhubung ({port})",
                position=pos,
                target=pos,
                anchor=pos,
                msg="Posisi saat ini dijadikan acuan jendela 1 putaran.",
            )

            while not stop_event.is_set():
                try:
                    cmd = _cmds.get(timeout=0.05)
                except queue.Empty:
                    cmd = None

                if cmd is not None:
                    snap = _snapshot()
                    if cmd[0] == "move":
                        wanted = snap["target"] + cmd[1]
                        limited = clamp_target(wanted, snap["anchor"])
                        if limited != wanted:
                            _set(msg="Batas 1 putaran (10.485.760 counts) tercapai.")
                        else:
                            _set(msg="")
                        if send_position(ser, limited):
                            _set(target=limited)
                        else:
                            _set(msg="Gagal mengirim perintah ke driver.")
                    elif cmd[0] == "set_center":
                        # Titik tengah baru = posisi riil sekarang; jendela dipindah ke sini.
                        _set(
                            anchor=snap["position"],
                            target=snap["position"],
                            msg=f"TENGAH ditandai: {snap['position']} counts.",
                        )
                        print(f"[centering] TENGAH (90 deg) = {snap['position']} counts")
                    elif cmd[0] == "disable":
                        disable_servo(ser)
                        _set(msg="Motor di-DISABLE (dilepas). Klik KIRI/KANAN untuk aktif lagi.")

                pos = read_position(ser, timeout=POLL_TIMEOUT, stop_event=stop_event)
                if pos is not None:
                    _set(position=pos)
    except (serial.SerialException, OSError) as err:
        _set(connected=False, status=f"Gagal buka {port}: {err}")
    finally:
        if _snapshot()["connected"]:
            _set(connected=False, status="Terputus")


def connect(port: str) -> None:
    global _worker
    disconnect()
    _stop_event.clear()
    while not _cmds.empty():
        _cmds.get_nowait()
    _set(connected=False, status=f"Menghubungkan ke {port}...", position=None,
         target=None, anchor=None, msg="")
    _worker = threading.Thread(target=_worker_loop, args=(port, _stop_event), daemon=True)
    _worker.start()


def disconnect() -> None:
    global _worker
    if _worker is not None and _worker.is_alive():
        _stop_event.set()
        _worker.join(timeout=2.0)
    _worker = None


# --- UI ---
def _step_counts() -> int:
    return deg_to_counts(float(dpg.get_value("step_radio")))


def _on_left() -> None:
    if _snapshot()["connected"]:
        _cmds.put(("move", +_step_counts()))   # counts positif = KIRI


def _on_right() -> None:
    if _snapshot()["connected"]:
        _cmds.put(("move", -_step_counts()))   # counts negatif = KANAN


def _on_set_center() -> None:
    if _snapshot()["connected"]:
        _cmds.put(("set_center",))


def _on_disable() -> None:
    if _snapshot()["connected"]:
        _cmds.put(("disable",))


def _on_connect() -> None:
    connect(dpg.get_value("port_input").strip())


def build_ui() -> None:
    with dpg.window(tag="main_window"):
        dpg.add_text("Centering Motor Servo KYDAS4801A")
        dpg.add_text("Tutup main.py dulu: port serial tidak bisa dipakai bersamaan.",
                     color=(255, 200, 80))
        dpg.add_separator()

        with dpg.group(horizontal=True):
            dpg.add_text("Port:")
            dpg.add_input_text(tag="port_input", default_value=SERIAL_PORT, width=110)
            dpg.add_button(label="Hubungkan", callback=_on_connect)
            dpg.add_button(label="Putuskan", callback=lambda: disconnect())
        dpg.add_text("", tag="status_text")
        dpg.add_separator()

        dpg.add_text("Posisi motor (counts):")
        dpg.add_text("-", tag="pos_text")
        dpg.add_text("Relatif ke TENGAH:")
        dpg.add_text("-", tag="rel_text")
        dpg.add_text("Rentang gerak (1 putaran = 10.485.760 counts):")
        dpg.add_progress_bar(tag="travel_bar", default_value=0.5, width=-1, overlay="-")
        dpg.add_separator()

        dpg.add_text("Besar langkah (derajat per klik):")
        dpg.add_radio_button(STEP_OPTIONS_DEG, tag="step_radio", horizontal=True,
                             default_value=DEFAULT_STEP_DEG)
        dpg.add_text("", tag="step_info")
        dpg.add_spacer(height=6)

        with dpg.group(horizontal=True):
            dpg.add_button(label="<<  KIRI", callback=_on_left, width=170, height=70)
            dpg.add_button(label="KANAN  >>", callback=_on_right, width=170, height=70)
        dpg.add_spacer(height=6)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Tandai TENGAH (90 deg)", callback=_on_set_center,
                           width=170, height=36)
            dpg.add_button(label="DISABLE motor", callback=_on_disable, width=170, height=36)
        dpg.add_spacer(height=6)

        dpg.add_text("", tag="center_text", color=(120, 220, 120))
        dpg.add_text("", tag="msg_text", color=(255, 200, 80), wrap=360)


def update_ui() -> None:
    snap = _snapshot()
    dpg.set_value("status_text", snap["status"])
    dpg.set_value("step_info", f"= {_step_counts()} counts per klik")
    dpg.set_value("msg_text", snap["msg"])

    pos, anchor = snap["position"], snap["anchor"]
    if snap["connected"] and pos is not None and anchor is not None:
        rel = pos - anchor
        dpg.set_value("pos_text", f"{pos}")
        dpg.set_value("rel_text", f"{rel:+d} counts  ({counts_to_deg(rel):+.3f} deg)")
        frac = (rel + HALF_TRAVEL_COUNTS) / MAX_TRAVEL_COUNTS
        dpg.set_value("travel_bar", max(0.0, min(1.0, frac)))
        dpg.configure_item("travel_bar", overlay=f"{rel:+d} / +-{HALF_TRAVEL_COUNTS}")
        dpg.set_value("center_text", f"Titik TENGAH saat ini: {anchor} counts")
    else:
        dpg.set_value("pos_text", "-")
        dpg.set_value("rel_text", "-")
        dpg.set_value("center_text", "")


def main() -> None:
    dpg.create_context()
    build_ui()
    dpg.create_viewport(title="Centering Motor Servo", width=420, height=620)
    dpg.setup_dearpygui()
    dpg.set_primary_window("main_window", True)
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        update_ui()
        dpg.render_dearpygui_frame()

    disconnect()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
