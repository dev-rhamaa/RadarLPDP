import atexit
import dearpygui.dearpygui as dpg

from app.setup import setup_dpg, initialize_queues_and_events, start_worker_threads
from app.callbacks import update_ui_from_queues, cleanup_and_exit, resize_callback
from app.external_process import start_worker, stop_worker
from config import EXTERNAL_WORKER
from widgets.PPI import create_ppi_widget


def create_main_layout():
    """Mendefinisikan dan membuat hanya widget PPI di dalam window utama."""
    with dpg.window(tag="Primary Window"):
        with dpg.group(horizontal=True):
            with dpg.group(tag="left_column"):
                with dpg.child_window(label="PPI Desktop", tag="ppi_window", no_scrollbar=True) as ppi_win:
                    create_ppi_widget(parent=ppi_win, width=-1, height=-1)


if __name__ == "__main__":
    # 0. Jalankan background worker eksternal (sebelum app utama)
    try:
        start_worker(EXTERNAL_WORKER)
    except Exception as e:
        print(f"[external_worker] gagal start: {e}")
    atexit.register(stop_worker)

    # 1. Inisialisasi Dear PyGui (viewport, tema, handler)
    setup_dpg()

    # 2. Buat layout UI utama (hanya PPI)
    create_main_layout()
    dpg.set_primary_window("Primary Window", True)

    # Panggil fullscreen dan resize setelah layout dibuat untuk menghindari error
    dpg.toggle_viewport_fullscreen()
    resize_callback()

    # 3. Siapkan queues dan threads untuk background processing
    queues, stop_event = initialize_queues_and_events()
    threads = start_worker_threads(queues, stop_event)

    # 4. Jalankan main loop
    while dpg.is_dearpygui_running():
        update_ui_from_queues(queues)  # Cek data baru dari worker
        dpg.render_dearpygui_frame()   # Render frame UI

    # 5. Cleanup setelah aplikasi ditutup
    cleanup_and_exit(stop_event, threads)
