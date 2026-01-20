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

def initialize_queues_and_events() -> Tuple[Dict[str, queue.Queue], threading.Event]:
    """Create all queues and events needed for threading.
    
    Returns:
        Tuple of (queues_dict, stop_event)
    """
    queues = {
        'ppi': queue.Queue(),
        'fft': queue.Queue(),
        'sinewave': queue.Queue()
    }
    stop_event = threading.Event()
    return queues, stop_event

def start_worker_threads(
    queues: Dict[str, queue.Queue],
    stop_event: threading.Event
) -> Dict[str, threading.Thread]:
    """Create and start all worker threads.
    
    Args:
        queues: Dictionary of queues for inter-thread communication
        stop_event: Event to signal thread shutdown
        
    Returns:
        Dictionary of worker threads
    """
    # Note: fft_data_worker also handles PPI data
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
            target=angle_worker,
            args=(queues['ppi'], stop_event),
            daemon=True,
            name="AngleWorker"
        )
    }

    for thread in threads.values():
        thread.start()
        
    return threads

def setup_dpg(
    title: str = 'Real-time Radar UI & Spectrum Analyzer',
    width: int = 1280,
    height: int = 720
) -> None:
    """Initialize Dear PyGui, viewport, theme, and handlers.
    
    Args:
        title: Window title
        width: Initial window width in pixels
        height: Initial window height in pixels
    """
    dpg.create_context()

    # Ensure global texture registry is available at root
    if not dpg.does_item_exist("texture_registry"):
        dpg.add_texture_registry(tag="texture_registry")

    # Preload logo textures before creating any window/layout
    _preload_textures()

    # Define global theme
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(
                dpg.mvStyleVar_WindowPadding,
                APP_PADDING, APP_PADDING
            )
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
            dpg.add_theme_style(
                dpg.mvStyleVar_ItemSpacing,
                APP_SPACING, APP_SPACING
            )
            dpg.add_theme_color(
                dpg.mvPlotCol_PlotBg,
                THEME_COLORS["background"]
            )
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
