"""Main entry point for Radar LPDP application.

Layout: menu bar (all controls + live status) over a two-column workspace of
display-only cards. See app/ui_shell.py for menus, Settings and shortcuts.
"""

# Third-party
import dearpygui.dearpygui as dpg

# Local - app modules
from app import settings, ui_shell
from app.callbacks import cleanup_and_exit, resize_callback, update_ui_from_queues
from app.servo_controller import reset_servo_state_on_startup
from app.setup import initialize_queues_and_events, setup_dpg, start_worker_threads

# Local - widgets
from widgets.FFT import create_fft_widget
from widgets.PPI import create_ppi_widget
from widgets.Sinewave import create_sinewave_widget
from widgets.logo import create_logo_widget
from widgets.metrics import create_metrics_widget


def _card(tag: str, builder) -> None:
    with dpg.child_window(tag=tag, border=True, no_scrollbar=True) as win:
        builder(parent=win, width=-1, height=-1)


def create_main_layout():
    """Primary window: menu bar + two columns of cards (sized by resize_callback)."""
    with dpg.window(tag="Primary Window", menubar=True, no_scrollbar=True):
        ui_shell.build_menu_bar()

        with dpg.group(horizontal=True, tag="main_content_group"):
            with dpg.group(tag="left_column"):
                _card("ppi_window", create_ppi_widget)
                _card("fft_window", create_fft_widget)

            with dpg.group(tag="right_column"):
                _card("sinewave_window", create_sinewave_widget)
                _card("metrics_window", create_metrics_widget)
                _card("logo_window", create_logo_widget)


# --- Titik Masuk Aplikasi --- #
if __name__ == "__main__":
    # 0. Motor servo selalu mulai dalam status STOPPED saat aplikasi dibuka
    reset_servo_state_on_startup()

    # 1. Inisialisasi Dear PyGui (viewport, tema, font) dan setting tersimpan
    setup_dpg()
    settings.load()

    # 2. Buat layout UI utama, lalu terapkan settings & shortcut
    create_main_layout()
    dpg.set_primary_window("Primary Window", True)
    ui_shell.init_shell()

    # Fullscreen & initial resize trigger
    dpg.toggle_viewport_fullscreen()
    resize_callback()

    # 3. Siapkan queues dan threads untuk background processing
    queues, stop_event = initialize_queues_and_events()
    threads = start_worker_threads(queues, stop_event)

    # 4. Jalankan main render loop
    while dpg.is_dearpygui_running():
        update_ui_from_queues(queues)
        ui_shell.tick()
        dpg.render_dearpygui_frame()

    # 5. Cleanup aman setelah aplikasi ditutup
    cleanup_and_exit(stop_event, threads)
