"""PPI (Plan Position Indicator) widget for radar display.

This module provides the tactical radar PPI display with radial azimuth spokes,
range rings, illuminated sweep line, and target plotting.
"""

import math
from typing import List, Tuple

import dearpygui.dearpygui as dpg
import numpy as np

from config import RADAR_MAX_RANGE, THEME_COLORS


def _create_ppi_themes():
    """Create dedicated plot themes for sweep line, rings, and target blips."""
    # Theme for radar sweep line (phosphor green glow)
    if not dpg.does_item_exist("ppi_sweep_theme"):
        with dpg.theme(tag="ppi_sweep_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, THEME_COLORS.get("accent_green", (0, 255, 157, 255)))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2.5)

    # Theme for detected targets (tactical crimson red marker)
    if not dpg.does_item_exist("ppi_target_theme"):
        with dpg.theme(tag="ppi_target_theme"):
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, (255, 59, 48, 255))
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (255, 75, 65, 220))
                dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 8.5)

    # Theme for reticle rings & azimuth lines (faint cyan)
    if not dpg.does_item_exist("ppi_reticle_theme"):
        with dpg.theme(tag="ppi_reticle_theme"):
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 210, 255, 80))
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.0)


def create_ppi_widget(parent, width, height):
    """Membuat widget PPI yang memaksimalkan area plot radar tanpa header berlebih."""
    _create_ppi_themes()

    axis_limit = int(RADAR_MAX_RANGE)

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

            # 1. Radial Azimuth Spokes (30°, 60°, 90°, 120°, 150°)
            for angle_deg in [30, 60, 90, 120, 150]:
                rad = math.radians(angle_deg)
                x_spoke = [0.0, axis_limit * math.cos(rad)]
                y_spoke = [0.0, axis_limit * math.sin(rad)]
                spoke_series = dpg.add_line_series(
                    x_spoke,
                    y_spoke,
                    parent=y_axis,
                    label=f"{angle_deg}°" if angle_deg in [30, 90, 150] else ""
                )
                dpg.bind_item_theme(spoke_series, "ppi_reticle_theme")

            # 2. Concentric Range Rings (e.g. 3, 6, 9, 12, 15 km)
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

            # 3. Dynamic Sweep Line (Illuminated phosphor green beam)
            sweep_line = dpg.add_line_series(
                [0.0, 0.0],
                [0.0, float(axis_limit)],
                label="Beam Sweep",
                tag="ppi_sweep_line",
                parent=y_axis
            )
            dpg.bind_item_theme(sweep_line, "ppi_sweep_theme")

            # 4. Detected Targets Series (Glowing tactical crimson blips)
            target_series = dpg.add_scatter_series(
                [],
                [],
                label="Acquired Targets",
                tag="ppi_target_series",
                parent=y_axis
            )
            dpg.bind_item_theme(target_series, "ppi_target_theme")


def update_sweep_line(angle: float) -> None:
    """Perbarui posisi garis sapuan beam radar."""
    if dpg.does_item_exist("ppi_sweep_line"):
        angle_rad = np.deg2rad(angle)
        x_end = float(RADAR_MAX_RANGE * np.cos(angle_rad))
        y_end = float(RADAR_MAX_RANGE * np.sin(angle_rad))
        dpg.set_value("ppi_sweep_line", ([0.0, x_end], [0.0, y_end]))


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
