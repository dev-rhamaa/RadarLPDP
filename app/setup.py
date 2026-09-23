"""Setup and initialization module for Dear PyGui application.

This module handles DearPyGui initialization, texture loading,
queue setup, and worker thread management.
"""

import os
import queue
import threading
from pathlib import Path
from typing import Dict, Tuple, Any

import dearpygui.dearpygui as dpg

from app.callbacks import resize_callback
from config import APP_SPACING, APP_PADDING, THEME_COLORS, PROJECT_ROOT
from functions.data_processing import fft_data_worker, sinewave_data_worker, angle_worker

def _preload_textures() -> None:
    """Load commonly used textures into the global texture registry."""
    if not dpg.does_item_exist("texture_registry"):
        dpg.add_texture_registry(tag="texture_registry")

    assets_dir = PROJECT_ROOT / "Assets"
    textures = [
        ("logo_lpdp", assets_dir / "Logo_LPDP.png"),
        ("logo_dkst", assets_dir / "DKST_ITB.png"),
        ("logo_kirei", assets_dir / "KIREI.png"),
    ]

    for tag, path in textures:
        if dpg.does_item_exist(tag):
            continue
            
        if not path.exists():
            print(f"[textures] File not found: {path}")
            continue
            
        try:
            width, height, channels, data = dpg.load_image(str(path))
            dpg.add_static_texture(
                width, height, data,
                tag=tag,
                parent="texture_registry"
            )
        except Exception as e:
            print(f"[textures] Failed to load {path}: {e}")

from app.c_acquisition import NativeCAcquisitionEngine

# Global native acquisition engine reference
_active_c_daq_engine = None

def get_active_daq_engine():
    """Get the active native C DAQ engine instance."""
    global _active_c_daq_engine
    return _active_c_daq_engine

def initialize_queues_and_events() -> Tuple[Dict[str, queue.Queue], threading.Event]:
    """Create all queues and events needed for threading.
    
    Returns:
        Tuple of (queues_dict, stop_event)
    """
    queues = {
        'ppi': queue.Queue(maxsize=50),
        'fft': queue.Queue(maxsize=2),
        'sinewave': queue.Queue(maxsize=2),
        'raw_fft': queue.Queue(maxsize=2),
        'raw_sinewave': queue.Queue(maxsize=2)
    }
    stop_event = threading.Event()
    return queues, stop_event

def start_worker_threads(
    queues: Dict[str, queue.Queue],
    stop_event: threading.Event
) -> Dict[str, Any]:
    """Create and start all worker threads including embedded C DAQ engine.
    
    Args:
        queues: Dictionary of queues for inter-thread communication
        stop_event: Event to signal thread shutdown
        
    Returns:
        Dictionary of worker threads
    """
    global _active_c_daq_engine

    # Callback when C DAQ card captures a continuous DMA event
    def on_daq_event(ch1, ch2, sample_rate):
        evt = {"ch1": ch1, "ch2": ch2, "sample_rate": sample_rate}
        for q in [queues.get('raw_fft'), queues.get('raw_sinewave')]:
            if q is not None:
                try:
                    if q.full():
                        try:
                            q.get_nowait()  # Drop oldest frame if full to prevent lag
                        except queue.Empty:
                            pass
                    q.put_nowait(evt)
                except Exception:
                    pass

    # Initialize embedded C DAQ engine
    c_daq = NativeCAcquisitionEngine(on_event_received=on_daq_event)
    _active_c_daq_engine = c_daq
    c_daq.start()

    # Note: fft_data_worker also handles PPI data
    threads = {
        'c_daq': c_daq,
        'fft': threading.Thread(
            target=fft_data_worker,
            args=(queues['fft'], queues['ppi'], stop_event, queues.get('raw_fft')),
            daemon=True,
            name="FFTWorker"
        ),
        'sinewave': threading.Thread(
            target=sinewave_data_worker,
            args=(queues['sinewave'], stop_event, queues.get('raw_sinewave')),
            daemon=True,
            name="SinewaveWorker"
        ),
        'angle': threading.Thread(
            target=angle_worker,
            args=(queues['ppi'], stop_event),
            daemon=True,
            name="AngleWorker"
        )
    }

    for name, item in threads.items():
        if isinstance(item, threading.Thread):
            item.start()
        
    return threads

def _setup_fonts() -> None:
    """Register modern anti-aliased system fonts for DearPyGui."""
    if not dpg.does_item_exist("font_registry"):
        with dpg.font_registry(tag="font_registry"):
            # Check standard Windows font paths
            font_segoe = "C:/Windows/Fonts/segoeui.ttf"
            font_segoe_bold = "C:/Windows/Fonts/segoeuib.ttf"
            font_consolas = "C:/Windows/Fonts/consola.ttf"

            has_segoe = os.path.exists(font_segoe)
            has_segoe_bold = os.path.exists(font_segoe_bold)
            has_consolas = os.path.exists(font_consolas)

            if has_segoe:
                dpg.add_font(font_segoe, 15, tag="font_default")
                dpg.bind_font("font_default")
            
            if has_segoe_bold:
                dpg.add_font(font_segoe_bold, 16, tag="font_bold")
                dpg.add_font(font_segoe_bold, 20, tag="font_title")

            if has_consolas:
                dpg.add_font(font_consolas, 14, tag="font_mono")


def setup_dpg(
    title: str = 'Radar Surveillance & Real-Time Spectrum C2 Console',
    width: int = 1440,
    height: int = 900
) -> None:
    """Initialize Dear PyGui, viewport, modern tactical theme, and handlers.
    
    Args:
        title: Window title
        width: Initial window width in pixels
        height: Initial window height in pixels
    """
    dpg.create_context()

    # Ensure global texture registry is available at root
    if not dpg.does_item_exist("texture_registry"):
        dpg.add_texture_registry(tag="texture_registry")

    # Load high-definition fonts
    _setup_fonts()

    # Preload logo textures before creating any window/layout
    _preload_textures()

    # Define modern military-grade tactical dark theme
    with dpg.theme(tag="global_theme") as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Modern roundings
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8.0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8.0)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4.0)

            # Modern breathing room
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8, 8)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 5)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 4)

            # Palette: Deep Tactical Dark
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, THEME_COLORS["background"])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, THEME_COLORS["card_bg"])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (22, 28, 42, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, THEME_COLORS["card_border"])
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))

            # Controls: Frames, Headers & Buttons
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (13, 18, 28, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (24, 34, 52, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (32, 45, 68, 255))
            
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (14, 20, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (20, 30, 48, 255))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (14, 20, 32, 255))

            dpg.add_theme_color(dpg.mvThemeCol_Button, (25, 36, 56, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (36, 52, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 180, 216, 255))

            dpg.add_theme_color(dpg.mvThemeCol_Header, (25, 36, 56, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (36, 52, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (0, 210, 255, 180))

            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, THEME_COLORS["accent_green"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, THEME_COLORS["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, THEME_COLORS["accent_green"])

            dpg.add_theme_color(dpg.mvThemeCol_Separator, THEME_COLORS["card_border"])
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, THEME_COLORS["accent"])

            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, THEME_COLORS["text"])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, THEME_COLORS["text_muted"])

            # Tables
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (24, 33, 52, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (45, 60, 88, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (28, 38, 56, 180))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (16, 21, 33, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (20, 26, 40, 255))

            # Plots
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, THEME_COLORS["plot_bg"])
            dpg.add_theme_color(dpg.mvPlotCol_PlotBorder, THEME_COLORS["card_border"])
            dpg.add_theme_color(dpg.mvPlotCol_LegendBg, (14, 20, 32, 220))
            dpg.add_theme_color(dpg.mvPlotCol_LegendBorder, THEME_COLORS["card_border"])
            dpg.add_theme_color(dpg.mvPlotCol_LegendText, THEME_COLORS["text"])

    dpg.bind_theme(global_theme)

    # Setup handler for Esc key to exit
    with dpg.handler_registry():
        dpg.add_key_press_handler(
            key=dpg.mvKey_Escape,
            callback=dpg.stop_dearpygui
        )

    # Configure viewport
    dpg.create_viewport(title=title, width=width, height=height)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_viewport_resize_callback(resize_callback)
