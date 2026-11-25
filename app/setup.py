"""Setup and initialization module for Dear PyGui application.

This module handles DearPyGui initialization, texture loading,
queue setup, and worker thread management.
"""

import queue
import threading
from typing import Dict, Tuple, Any

import dearpygui.dearpygui as dpg

from app.c_acquisition import NativeCAcquisitionEngine
from app.callbacks import resize_callback
from app.fonts import setup_fonts
from config import (
    THEME_COLORS, PROJECT_ROOT,
)
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
            width, height, _channels, data = dpg.load_image(str(path))
            dpg.add_static_texture(
                width, height, data,
                tag=tag,
                parent="texture_registry"
            )
        except Exception as e:
            print(f"[textures] Failed to load {path}: {e}")

def _create_global_theme() -> None:
    """Calm modern dark theme: soft surfaces, generous spacing, one meaning per accent."""
    c = THEME_COLORS
    with dpg.theme(tag="global_theme") as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Shape
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10.0)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10.0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8.0)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6.0)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0.0)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1.0)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1.0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0.0)

            # Spacing
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 5)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 10)

            # Surfaces
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, c["background"])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, c["card_bg"])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (26, 30, 42, 252))
            dpg.add_theme_color(dpg.mvThemeCol_ModalWindowDimBg, (5, 7, 12, 170))
            dpg.add_theme_color(dpg.mvThemeCol_Border, c["card_border"])
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, c["card_bg"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, c["card_bg"])
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, c["card_bg"])
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (0, 0, 0, 0))

            # Controls
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, c["surface_hi"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, c["surface_hover"])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (52, 58, 78, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, c["surface_hi"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, c["surface_hover"])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (139, 146, 240, 120))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (139, 146, 240, 50))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (139, 146, 240, 80))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (139, 146, 240, 120))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, c["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, c["accent_violet"])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, c["accent"])
            dpg.add_theme_color(dpg.mvThemeCol_Separator, c["card_border"])
            dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, c["accent_violet"])
            dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, c["accent_violet"])

            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, c["text"])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, c["text_muted"])

            # Tables: no heavy grid, subtle header
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (30, 35, 48, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, c["card_border"])
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (38, 44, 58, 160))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (255, 255, 255, 6))

        with dpg.theme_component(dpg.mvAll):
            # Plots blend into the card: no frame, faint grid, muted axis text
            dpg.add_theme_color(dpg.mvPlotCol_FrameBg, (0, 0, 0, 0), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, c["plot_bg"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_PlotBorder, (0, 0, 0, 0), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_AxisGrid, c["grid_lines"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_AxisText, c["text_muted"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendBg, (22, 26, 36, 200), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendBorder, (0, 0, 0, 0), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendText, c["text_muted"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_InlayText, c["text_muted"], category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_Crosshairs, (226, 232, 240, 90), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, 4, 4, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LegendPadding, 8, 6, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.6, category=dpg.mvThemeCat_Plots)

    dpg.bind_theme(global_theme)


# Global native acquisition engine reference
_active_c_daq_engine = None

def get_active_daq_engine():
    """Get the active native C DAQ engine instance."""
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

    for item in threads.values():
        if isinstance(item, threading.Thread):
            item.start()
        
    return threads

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
    setup_fonts()

    # Preload logo textures before creating any window/layout
    _preload_textures()

    _create_global_theme()

    # Configure viewport
    dpg.create_viewport(title=title, width=width, height=height)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_viewport_resize_callback(resize_callback)
