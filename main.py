"""Main entry point for Radar LPDP application.

This file defines the functional radar layout, sleek status ribbon, and runs the main loop.
"""

# Third-party
import dearpygui.dearpygui as dpg

# Local - app modules
from app.callbacks import cleanup_and_exit, resize_callback, update_ui_from_queues
from app.setup import initialize_queues_and_events, setup_dpg, start_worker_threads

# Local - widgets
from widgets.FFT import create_fft_widget
from widgets.PPI import create_ppi_widget
from widgets.Sinewave import create_sinewave_widget
from widgets.logo import create_logo_widget
from widgets.metrics import create_metrics_widget


def create_top_header():
    """Membuat status ribbon ramping di bagian paling atas aplikasi (height=36)."""
    with dpg.child_window(tag="top_header_bar", height=36, border=True, no_scrollbar=True):
        with dpg.group(horizontal=True):
            dpg.add_text("📡 FMCW RADAR C2", color=(0, 210, 255))
            if dpg.does_item_exist("font_bold"):
                dpg.bind_item_font(dpg.last_item(), "font_bold")

            dpg.add_spacer(width=12)
            dpg.add_text("│", color=(48, 64, 94))
            dpg.add_spacer(width=12)

            dpg.add_text("● PCI-9846H: 20 MS/s", color=(0, 255, 157))
            dpg.add_spacer(width=12)
            dpg.add_text("● ZERO-COPY DMA", color=(0, 210, 255))
            dpg.add_spacer(width=12)
            dpg.add_text("● EXT-D TRIGGER", color=(255, 184, 0))

            dpg.add_spacer(width=16)
            dpg.add_text("│", color=(48, 64, 94))
            dpg.add_spacer(width=16)

            dpg.add_text("STREAM:", color=(130, 145, 170))
            dpg.add_text("0.0 FPS", color=(0, 210, 255), tag="header_fps_count")
            if dpg.does_item_exist("font_mono"):
                dpg.bind_item_font(dpg.last_item(), "font_mono")

            dpg.add_spacer(width=12)
            dpg.add_text("EVENTS:", color=(130, 145, 170))
            dpg.add_text("0 EVT", color=(240, 246, 255), tag="header_event_count")
            if dpg.does_item_exist("font_mono"):
                dpg.bind_item_font(dpg.last_item(), "font_mono")

            dpg.add_spacer(width=12)
            dpg.add_text("--:--:--", color=(140, 155, 180), tag="header_system_time")
            if dpg.does_item_exist("font_mono"):
                dpg.bind_item_font(dpg.last_item(), "font_mono")


def create_main_layout():
    """Mendefinisikan dan membuat semua widget fungsional di dalam window utama."""
    with dpg.window(tag="Primary Window", no_scrollbar=True):
        # 1. Sleek Single-Line Status Ribbon
        create_top_header()
        dpg.add_spacer(height=2)

        # 2. Functional Two-Column Workspace (Maximizing Canvas Space)
        with dpg.group(horizontal=True, tag="main_content_group"):
            # Kolom kiri: Layar PPI Radar Taktis & Spektrum Frekuensi FFT
            with dpg.group(tag="left_column"):
                with dpg.child_window(label="PPI Radar Display (0 - 15 km)", tag="ppi_window", no_scrollbar=True) as ppi_win:
                    create_ppi_widget(parent=ppi_win, width=-1, height=-1)
                with dpg.child_window(label="Beat Frequency Spectrum Analyzer", tag="fft_window", no_scrollbar=True) as fft_win:
                    create_fft_widget(parent=fft_win, width=-1, height=-1)

            # Kolom kanan: Osiloskop, Telemetri Target, dan Logo
            with dpg.group(tag="right_column"):
                with dpg.child_window(label="Time-Domain Oscilloscope (CH0 & CH2)", tag="sinewave_window", no_scrollbar=True) as sinewave_win:
                    create_sinewave_widget(parent=sinewave_win, width=-1, height=-1)
                with dpg.child_window(label="Radar Target Telemetry & Detection", tag="metrics_window", no_scrollbar=True) as metrics_win:
                    create_metrics_widget(parent=metrics_win, width=-1, height=-1)
                with dpg.child_window(label="Institutional Affiliation", tag="logo_window", no_scrollbar=True) as logo_win:
                    create_logo_widget(parent=logo_win, width=-1, height=-1)


# --- Titik Masuk Aplikasi --- #
if __name__ == "__main__":
    # 1. Inisialisasi Dear PyGui (viewport, tema taktis, font HD, handler)
    setup_dpg()

    # 2. Buat layout UI utama
    create_main_layout()
    dpg.set_primary_window("Primary Window", True)

    # Fullscreen & initial resize trigger
    dpg.toggle_viewport_fullscreen()
    resize_callback()

    # 3. Siapkan queues dan threads untuk background processing
    queues, stop_event = initialize_queues_and_events()
    threads = start_worker_threads(queues, stop_event)

    # 4. Jalankan main render loop
    while dpg.is_dearpygui_running():
        update_ui_from_queues(queues)
        dpg.render_dearpygui_frame()

    # 5. Cleanup aman setelah aplikasi ditutup
    cleanup_and_exit(stop_event, threads)