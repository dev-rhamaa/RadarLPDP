"""PPI (Plan Position Indicator) widget for radar display.

Provides tactical radar PPI display with manual servo target position input & auto scan toggle.
"""

import math
from typing import List, Tuple

import dearpygui.dearpygui as dpg
import numpy as np

from config import RADAR_MAX_RANGE, THEME_COLORS
from app.servo_controller import (
    set_servo_target_degrees,
    set_servo_mode,
    get_servo_state,
    set_servo_running,
    is_servo_running,
)


def _create_ppi_themes():
    """Create dedicated plot themes for sweep line, rings, target blips, and control buttons."""
    if not dpg.does_item_exist("ppi_sweep_theme"):
        with dpg.theme(tag="ppi_sweep_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, THEME_COLORS.get("accent_green", (0, 255, 157, 255)))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2.5)

    if not dpg.does_item_exist("ppi_target_theme"):
        with dpg.theme(tag="ppi_target_theme"):
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, (255, 59, 48, 255))
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (255, 75, 65, 220))
                dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 8.5)

    if not dpg.does_item_exist("ppi_reticle_theme"):
        with dpg.theme(tag="ppi_reticle_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 210, 255, 80))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.0)

    if not dpg.does_item_exist("ppi_start_btn_theme"):
        with dpg.theme(tag="ppi_start_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (16, 92, 54, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (22, 128, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 255, 157, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (240, 255, 245, 255))

    if not dpg.does_item_exist("ppi_stop_btn_theme"):
        with dpg.theme(tag="ppi_stop_btn_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (110, 24, 24, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (150, 32, 32, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (255, 59, 48, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 240, 240, 255))


def _update_servo_ui_status(running: bool):
    """Update UI labels and colors for servo running/stopped state."""
    if dpg.does_item_exist("servo_status_text"):
        if running:
            dpg.set_value("servo_status_text", "● RUNNING")
            dpg.configure_item("servo_status_text", color=(0, 255, 157))
        else:
            dpg.set_value("servo_status_text", "● STOPPED")
            dpg.configure_item("servo_status_text", color=(255, 59, 48))

    if dpg.does_item_exist("header_motor_status"):
        if running:
            dpg.set_value("header_motor_status", "RUNNING")
            dpg.configure_item("header_motor_status", color=(0, 255, 157))
        else:
            dpg.set_value("header_motor_status", "STOPPED")
            dpg.configure_item("header_motor_status", color=(255, 59, 48))


def _on_start_clicked():
    """Callback when user clicks MULAI button."""
    # Pastikan mode di backend selalu sinkron dengan pilihan radio button di UI
    if dpg.does_item_exist("servo_mode_radio"):
        ui_mode = dpg.get_value("servo_mode_radio")
        mode_str = "scan" if ui_mode == "AUTO SCAN" else "manual"
        set_servo_mode(mode_str)
        if mode_str == "manual" and dpg.does_item_exist("servo_target_slider"):
            deg = float(dpg.get_value("servo_target_slider"))
            set_servo_target_degrees(deg)
    set_servo_running(True)
    _update_servo_ui_status(True)


def _on_stop_clicked():
    """Callback when user clicks STOP button."""
    set_servo_running(False)
    _update_servo_ui_status(False)
    if dpg.does_item_exist("servo_target_slider"):
        dpg.set_value("servo_target_slider", 90.0)


def _on_target_slider_changed(sender, app_data):
    """Callback when user changes manual target slider."""
    deg = float(app_data)
    set_servo_target_degrees(deg)
    if dpg.does_item_exist("servo_mode_radio"):
        dpg.set_value("servo_mode_radio", "MANUAL")


def _on_mode_radio_changed(sender, app_data):
    """Callback when user toggles between AUTO SCAN and MANUAL."""
    mode_str = "scan" if app_data == "AUTO SCAN" else "manual"
    set_servo_mode(mode_str)


def _set_preset_angle(deg: float):
    """Quick preset button callback."""
    set_servo_target_degrees(deg)
    if dpg.does_item_exist("servo_target_slider"):
        dpg.set_value("servo_target_slider", deg)
    if dpg.does_item_exist("servo_mode_radio"):
        dpg.set_value("servo_mode_radio", "MANUAL")


def create_ppi_widget(parent, width, height):
    """Membuat widget PPI lengkap dengan panel kendali posisi target antena servo."""
    _create_ppi_themes()

    axis_limit = int(RADAR_MAX_RANGE)

    # 1. Sleek Tactical Antenna Steering Control Bar with MULAI & STOP Buttons
    with dpg.group(parent=parent, horizontal=True):
        dpg.add_text("MOTOR:", color=(0, 210, 255))
        if dpg.does_item_exist("font_bold"):
            dpg.bind_item_font(dpg.last_item(), "font_bold")

        start_btn = dpg.add_button(
            label="MULAI",
            tag="servo_start_btn",
            callback=_on_start_clicked,
            width=58
        )
        dpg.bind_item_theme(start_btn, "ppi_start_btn_theme")

        stop_btn = dpg.add_button(
            label="STOP",
            tag="servo_stop_btn",
            callback=_on_stop_clicked,
            width=52
        )
        dpg.bind_item_theme(stop_btn, "ppi_stop_btn_theme")

        init_running = is_servo_running()
        status_label = "● RUNNING" if init_running else "● STOPPED"
        status_color = (0, 255, 157) if init_running else (255, 59, 48)
        dpg.add_text(status_label, color=status_color, tag="servo_status_text")
        if dpg.does_item_exist("font_mono"):
            dpg.bind_item_font(dpg.last_item(), "font_mono")

        dpg.add_spacer(width=8)
        dpg.add_text("│", color=(48, 64, 94))
        dpg.add_spacer(width=8)

        init_state = get_servo_state()
        init_mode = "AUTO SCAN" if init_state.get("mode", "scan") == "scan" else "MANUAL"

        dpg.add_text("MODE:", color=(130, 145, 170))
        dpg.add_radio_button(
            ["AUTO SCAN", "MANUAL"],
            default_value=init_mode,
            horizontal=True,
            tag="servo_mode_radio",
            callback=_on_mode_radio_changed
        )
        dpg.add_spacer(width=8)
        dpg.add_text("TARGET:", color=(130, 145, 170))
        dpg.add_slider_float(
            min_value=0.0,
            max_value=180.0,
            default_value=90.0,
            format="%.1f deg",
            width=115,
            tag="servo_target_slider",
            callback=_on_target_slider_changed
        )
        dpg.add_spacer(width=4)
        dpg.add_button(label="0 deg", callback=lambda: _set_preset_angle(0.0), width=44)
        dpg.add_button(label="45 deg", callback=lambda: _set_preset_angle(45.0), width=44)
        dpg.add_button(label="90 deg", callback=lambda: _set_preset_angle(90.0), width=44)
        dpg.add_button(label="135 deg", callback=lambda: _set_preset_angle(135.0), width=44)
        dpg.add_button(label="180 deg", callback=lambda: _set_preset_angle(180.0), width=44)

    dpg.add_spacer(parent=parent, height=2)

    # 2. Polar Tactical PPI Radar Plot
    with dpg.plot(
        label="Plan Position Indicator (0 - 15 km)",
        parent=parent,
        width=-1,
        height=-1,
        equal_aspects=True,
        tag="ppi_plot_widget"
    ):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)

        x_axis = dpg.add_plot_axis(
            dpg.mvXAxis,
            label="",
            no_tick_labels=True,
            lock_min=True,
            lock_max=True
        )
        dpg.set_axis_limits(x_axis, -axis_limit, axis_limit)

        y_axis = dpg.add_plot_axis(
            dpg.mvYAxis,
            label="",
            no_tick_labels=True,
            lock_min=True,
            lock_max=True
        )
        dpg.set_axis_limits(y_axis, 0, axis_limit)

        # Radial Azimuth Spokes (30°, 60°, 90°, 120°, 150°)
        for angle_deg in [30, 60, 90, 120, 150]:
            rad = math.radians(angle_deg)
            x_spoke = [0.0, axis_limit * math.cos(rad)]
            y_spoke = [0.0, axis_limit * math.sin(rad)]
            spoke_series = dpg.add_line_series(
                x_spoke,
                y_spoke,
                parent=y_axis,
                label=f"{angle_deg} deg" if angle_deg in [30, 90, 150] else ""
            )
            dpg.bind_item_theme(spoke_series, "ppi_reticle_theme")

        # Concentric Range Rings (e.g. 3, 6, 9, 12, 15 km)
        theta = np.linspace(0, np.pi, 120)
        step = max(int(axis_limit // 5), 1)
        for r in range(step, axis_limit + 1, step):
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            ring_series = dpg.add_line_series(
                list(x),
                list(y),
                parent=y_axis,
                label=f"{r} km"
            )
            dpg.bind_item_theme(ring_series, "ppi_reticle_theme")

        # Dynamic Sweep Line (Illuminated phosphor green beam)
        sweep_line = dpg.add_line_series(
            [0.0, 0.0],
            [0.0, float(axis_limit)],
            label="Beam Sweep",
            tag="ppi_sweep_line",
            parent=y_axis
        )
        dpg.bind_item_theme(sweep_line, "ppi_sweep_theme")

        # Detected Targets Series (Glowing tactical crimson blips)
        target_series = dpg.add_scatter_series(
            [],
            [],
            label="Acquired Targets",
            tag="ppi_target_series",
            parent=y_axis
        )
        dpg.bind_item_theme(target_series, "ppi_target_theme")


def update_sweep_line(angle: float) -> None:
    """Perbarui posisi garis sapuan beam radar mengikuti pembacaan encoder servo."""
    if dpg.does_item_exist("ppi_sweep_line"):
        angle_rad = np.deg2rad(angle)
        x_end = float(RADAR_MAX_RANGE * np.cos(angle_rad))
        y_end = float(RADAR_MAX_RANGE * np.sin(angle_rad))
        dpg.set_value("ppi_sweep_line", ([0.0, x_end], [0.0, y_end]))

    if dpg.does_item_exist("header_azimuth_angle"):
        dpg.set_value("header_azimuth_angle", f"{angle:5.1f} deg")


def add_target_to_plot(targets: List[Tuple[float, float]]) -> None:
    """Menggambar semua target yang ada dalam riwayat."""
    if dpg.does_item_exist("ppi_target_series"):
        if targets:
            target_angles_rad = np.deg2rad([t[0] for t in targets])
            target_distances = [t[1] for t in targets]

            x_coords = target_distances * np.cos(target_angles_rad)
            y_coords = target_distances * np.sin(target_angles_rad)

            x_coords = np.ascontiguousarray(x_coords, dtype=np.float64)
            y_coords = np.ascontiguousarray(y_coords, dtype=np.float64)

            dpg.set_value('ppi_target_series', (x_coords, y_coords))
        else:
            dpg.set_value('ppi_target_series', ([], []))
