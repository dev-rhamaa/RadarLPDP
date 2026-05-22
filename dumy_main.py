"""Dummy entry point for Radar LPDP application.

This file is responsible for defining the UI layout and running the application
in simulation mode, where the sweep needle sweeps automatically back-and-forth 
without requiring any serial connection, and the data generator runs automatically in the background.
"""

# Standard library
import atexit
import queue
import sys
import threading
import time

# Third-party
import dearpygui.dearpygui as dpg

# Local - app modules
from app.callbacks import cleanup_and_exit, resize_callback, update_ui_from_queues
from app.external_process import start_worker, stop_worker
from app.setup import initialize_queues_and_events, setup_dpg

# Local - config
import config
from config import EXTERNAL_WORKER

# Local - widgets
from widgets.FFT import create_fft_widget
from widgets.PPI import create_ppi_widget
from widgets.Sinewave import create_sinewave_widget
from widgets.file import create_file_explorer_widget
from widgets.logo import create_logo_widget
from widgets.metrics import create_metrics_widget

# Local - data processing workers
from functions.data_processing import fft_data_worker, sinewave_data_worker


# --- Custom Dummy Angle Worker --- #
def dumy_angle_worker(ppi_queue: queue.Queue, stop_event: threading.Event) -> None:
    """Simulates rotor sweeps automatically back-and-forth between 0 and 180 degrees.
    
    This replaces the serial angle_worker and provides smooth, continuous 
    sweep needle animation for testing/demonstration purposes.
    
    Args:
        ppi_queue: Queue for sending angle updates
        stop_event: Event to signal worker shutdown
    """
    angle = 0.0
    direction = 1  # 1 = forward (0 -> 180), -1 = backward (180 -> 0)
    
    # 50 Hz update rate (smooth sweep). 
    # At 50 Hz, increment of 1.2 degrees per step takes exactly 3 seconds for a 180-degree sweep.
    increment = 1.2
    update_interval = 0.02  # 20ms
    
    print("[dumy_angle_worker] Automated sweep started.")
    
    while not stop_event.is_set():
        try:
            # Send calibrated angle to PPI queue
            ppi_queue.put({"type": "sweep", "angle": angle})
            
            # Update angle for next iteration
            angle += increment * direction
            
            # Detect limits and reverse direction
            if angle >= 180.0:
                angle = 180.0
                direction = -1
            elif angle <= 0.0:
                angle = 0.0
                direction = 1
                
            time.sleep(update_interval)
            
        except Exception as e:
            print(f"[dumy_angle_worker] Error: {e}")
            time.sleep(1.0)


# --- Custom Thread Starter for Simulation --- #
def start_dumy_worker_threads(
    queues: dict[str, queue.Queue],
    stop_event: threading.Event
) -> dict[str, threading.Thread]:
    """Create and start worker threads using the dummy automated angle sweep.
    
    Args:
        queues: Dictionary of queues for inter-thread communication
        stop_event: Event to signal thread shutdown
        
    Returns:
        Dictionary of running threads
    """
    threads = {
        'fft': threading.Thread(
            target=fft_data_worker,
            args=(queues['fft'], queues['ppi'], stop_event),
            daemon=True,
            name="FFTWorker"
        ),
        'sinewave': threading.Thread(
            target=sinewave_data_worker,
            args=(queues['sinewave'], stop_event),
            daemon=True,
            name="SinewaveWorker"
        ),
        'angle': threading.Thread(
            target=dumy_angle_worker,
            args=(queues['ppi'], stop_event),
            daemon=True,
            name="DumyAngleWorker"
        )
    }

    for thread in threads.values():
        thread.start()
        
    return threads


# --- Definisi Layout UI --- #
def create_main_layout():
    """Mendefinisikan dan membuat semua widget di dalam window utama."""
    with dpg.window(tag="Primary Window"):
        with dpg.group(horizontal=True):
            # Kolom kiri
            with dpg.group(tag="left_column"):
                with dpg.child_window(label="PPI Desktop", tag="ppi_window", no_scrollbar=True) as ppi_win:
                    create_ppi_widget(parent=ppi_win, width=-1, height=-1)
                with dpg.child_window(label="FFT Desktop", tag="fft_window", no_scrollbar=True) as fft_win:
                    create_fft_widget(parent=fft_win, width=-1, height=-1)
            
            # Kolom kanan
            with dpg.group(tag="right_column"):
                with dpg.child_window(label="Sinewave", tag="sinewave_window", no_scrollbar=True) as sinewave_win:
                    create_sinewave_widget(parent=sinewave_win, width=-1, height=-1)
                with dpg.child_window(label="Frequency Metrics", tag="metrics_window", no_scrollbar=True) as metrics_win:
                    create_metrics_widget(parent=metrics_win, width=-1, height=-1)
                with dpg.child_window(label="File Explorer", tag="file_explorer_window", no_scrollbar=True) as file_explorer_win:
                    create_file_explorer_widget(parent=file_explorer_win, width=-1, height=-1)
                with dpg.child_window(label="logo", tag="logo_window", no_scrollbar=True) as logo_win:
                    create_logo_widget(parent=logo_win, width=-1, height=-1)


# --- Titik Masuk Aplikasi --- #
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 RadarLPDP - DUMMY SIMULATOR MODE")
    print("=" * 60)
    
    # 0. Override EXTERNAL_WORKER to run the python simulator 'dumy_gen.py' automatically!
    config.EXTERNAL_WORKER = {
        "enabled": True,
        "exe_name": sys.executable,  # Uses the active Python environment interpreter
        "args": ["dumy_gen.py"],     # Command arguments to run the dummy data generator
        "cwd": str(config.PROJECT_ROOT),
        "env": {},
        "only_on_platforms": [],     # Runs on Windows, macOS, or Linux
    }
    
    # Jalankan background worker eksternal (simulator data biner)
    try:
        pid = start_worker(config.EXTERNAL_WORKER)
        if pid:
            print(f"[external_worker] Simulator data (dumy_gen.py) berhasil dijalankan, PID: {pid}")
    except Exception as e:
        print(f"[external_worker] gagal start: {e}")
    atexit.register(stop_worker)

    # 1. Inisialisasi Dear PyGui (viewport, tema, handler)
    setup_dpg()

    # 2. Buat layout UI utama
    create_main_layout()
    dpg.set_primary_window("Primary Window", True)

    # Panggil fullscreen dan resize setelah layout dibuat untuk menghindari error
    dpg.toggle_viewport_fullscreen()
    resize_callback()

    # 3. Siapkan queues dan threads khusus dummy
    queues, stop_event = initialize_queues_and_events()
    threads = start_dumy_worker_threads(queues, stop_event)

    # 4. Jalankan main loop
    while dpg.is_dearpygui_running():
        update_ui_from_queues(queues)  # Cek data baru dari worker
        dpg.render_dearpygui_frame()   # Render frame UI

    # 5. Cleanup setelah aplikasi ditutup
    cleanup_and_exit(stop_event, threads)
