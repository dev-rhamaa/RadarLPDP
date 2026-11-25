"""PPI (Plan Position Indicator) widget for radar display.

Display-only card: sector, range rings, azimuth spokes, beam sweep, and target
blips. Motor control and display options live in the menu bar (app/ui_shell.py).
"""

import math
from typing import List, Tuple

import dearpygui.dearpygui as dpg
import numpy as np

from config import RADAR_MAX_RANGE, RADAR_SWEEP_ANGLE_MAX, RADAR_SWEEP_ANGLE_MIN, THEME_COLORS
from widgets.common import card_header, line_theme

RING_STEP_KM = 3
SPOKE_ANGLES = [30, 60, 90, 120, 150]


def _create_ppi_themes():
    accent = THEME_COLORS["accent"]
    line_theme("ppi_sweep_theme", accent, 2.6)
    line_theme("ppi_reticle_theme", (120, 135, 165, 55), 1.0)
    line_theme("ppi_sector_border_theme", (120, 135, 165, 120), 1.4)

    if not dpg.does_item_exist("ppi_sector_fill_theme"):
        with dpg.theme(tag="ppi_sector_fill_theme"):
            with dpg.theme_component(dpg.mvShadeSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Fill, (accent[0], accent[1], accent[2], 10),
                                    category=dpg.mvThemeCat_Plots)

    if not dpg.does_item_exist("ppi_target_theme"):
        danger = THEME_COLORS["danger"]
        with dpg.theme(tag="ppi_target_theme"):
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, danger, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (danger[0], danger[1], danger[2], 200),
                                    category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle,
                                    category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 5.0, category=dpg.mvThemeCat_Plots)


def _polar(angle_deg: float, r: float) -> Tuple[float, float]:
    """Radar angle (0 deg = left, 90 deg = up, 180 deg = right) -> plot x/y."""
    rad = math.radians(180.0 - angle_deg)
    return r * math.cos(rad), r * math.sin(rad)


def create_ppi_widget(parent, width, height):
    """PPI card: header + polar plot of the 30-150 deg sector."""
    _create_ppi_themes()

    r_max = float(RADAR_MAX_RANGE)
    a_min, a_max = RADAR_SWEEP_ANGLE_MIN, RADAR_SWEEP_ANGLE_MAX

    card_header(parent, "PPI Radar", f"Sector {a_min:.0f}-{a_max:.0f}°  ·  0-{r_max:.0f} km",
                readout_tag="ppi_header_readout", readout_default="AZ  90.0°  ·  0 targets")

    with dpg.plot(parent=parent, width=-1, height=-1, equal_aspects=True, no_title=True,
                  no_menus=True, no_mouse_pos=True, no_box_select=True, tag="ppi_plot_widget"):
        pad = r_max * 0.08
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, no_tick_labels=True, no_gridlines=True,
                                   no_tick_marks=True, lock_min=True, lock_max=True)
        dpg.set_axis_limits(x_axis, -r_max - pad, r_max + pad)
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, no_tick_labels=True, no_gridlines=True,
                                   no_tick_marks=True, lock_min=True, lock_max=True)
        dpg.set_axis_limits(y_axis, -pad * 0.5, r_max + pad)

        # Subtle sector fill: between the boundary spokes and the outer arc
        edge_x = r_max * math.cos(math.radians(a_min))
        xs = np.linspace(-edge_x, edge_x, 160)
        tan_edge = math.tan(math.radians(a_min))
        lower = np.abs(xs) * tan_edge
        upper = np.sqrt(np.maximum(r_max ** 2 - xs ** 2, 0.0))
        fill = dpg.add_shade_series(list(xs), list(upper), y2=list(lower), parent=y_axis)
        dpg.bind_item_theme(fill, "ppi_sector_fill_theme")

        # Azimuth spokes + angle labels just beyond the outer ring
        for angle in SPOKE_ANGLES:
            x_end, y_end = _polar(angle, r_max)
            boundary = angle in (a_min, a_max)
            spoke = dpg.add_line_series([0.0, x_end], [0.0, y_end], parent=y_axis, tag=f"ppi_spoke_{angle}")
            dpg.bind_item_theme(spoke, "ppi_sector_border_theme" if boundary else "ppi_reticle_theme")
            lx, ly = _polar(angle, r_max + pad * 0.45)
            dpg.add_plot_annotation(label=f"{angle}°", default_value=(lx, ly), color=(0, 0, 0, 0),
                                    clamped=False, tag=f"ppi_spoke_label_{angle}", parent="ppi_plot_widget")

        # Range rings (arcs within the sector) + labels along the right boundary
        theta = np.linspace(math.radians(a_min), math.radians(a_max), 120)
        for r in range(RING_STEP_KM, int(r_max) + 1, RING_STEP_KM):
            ring = dpg.add_line_series(list(r * np.cos(theta)), list(r * np.sin(theta)),
                                       parent=y_axis, tag=f"ppi_ring_{r}")
            dpg.bind_item_theme(ring, "ppi_sector_border_theme" if r == int(r_max) else "ppi_reticle_theme")
            lx, ly = _polar(a_max, r)
            dpg.add_plot_annotation(label=f"{r} km", default_value=(lx, ly), offset=(14, 8),
                                    color=(0, 0, 0, 0), clamped=False, tag=f"ppi_ring_label_{r}",
                                    parent="ppi_plot_widget")

        sweep = dpg.add_line_series([0.0, 0.0], [0.0, r_max], tag="ppi_sweep_line", parent=y_axis)
        dpg.bind_item_theme(sweep, "ppi_sweep_theme")

        targets = dpg.add_scatter_series([], [], tag="ppi_target_series", parent=y_axis)
        dpg.bind_item_theme(targets, "ppi_target_theme")


def _ring_radii() -> List[int]:
    return list(range(RING_STEP_KM, int(RADAR_MAX_RANGE) + 1, RING_STEP_KM))


def set_rings_visible(show: bool) -> None:
    for r in _ring_radii():
        if r != int(RADAR_MAX_RANGE) and dpg.does_item_exist(f"ppi_ring_{r}"):
            dpg.configure_item(f"ppi_ring_{r}", show=show)


def set_ring_labels_visible(show: bool) -> None:
    for r in _ring_radii():
        if dpg.does_item_exist(f"ppi_ring_label_{r}"):
            dpg.configure_item(f"ppi_ring_label_{r}", show=show)
    for angle in SPOKE_ANGLES:
        if dpg.does_item_exist(f"ppi_spoke_label_{angle}"):
            dpg.configure_item(f"ppi_spoke_label_{angle}", show=show)


def set_spokes_visible(show: bool) -> None:
    for angle in SPOKE_ANGLES:
        if angle in (RADAR_SWEEP_ANGLE_MIN, RADAR_SWEEP_ANGLE_MAX):
            continue  # sector boundary always visible
        if dpg.does_item_exist(f"ppi_spoke_{angle}"):
            dpg.configure_item(f"ppi_spoke_{angle}", show=show)


_last_angle: float = 90.0
_last_target_count: int = 0


def _refresh_header() -> None:
    if dpg.does_item_exist("ppi_header_readout"):
        dpg.set_value("ppi_header_readout", f"AZ {_last_angle:5.1f}°  ·  {_last_target_count} targets")


def update_sweep_line(angle: float) -> None:
    """Move the beam to the servo encoder angle (0 deg left, 180 deg right)."""
    global _last_angle
    if dpg.does_item_exist("ppi_sweep_line"):
        clamped = max(RADAR_SWEEP_ANGLE_MIN, min(RADAR_SWEEP_ANGLE_MAX, float(angle)))
        x_end, y_end = _polar(clamped, float(RADAR_MAX_RANGE))
        dpg.set_value("ppi_sweep_line", ([0.0, x_end], [0.0, y_end]))

    _last_angle = float(angle)
    _refresh_header()
    if dpg.does_item_exist("header_azimuth_angle"):
        dpg.set_value("header_azimuth_angle", f"AZ {angle:5.1f}°")


def add_target_to_plot(targets: List[Tuple[float, float]]) -> None:
    """Draw every target in history that lies inside the sector."""
    global _last_target_count
    if not dpg.does_item_exist("ppi_target_series"):
        return
    valid = [t for t in (targets or []) if RADAR_SWEEP_ANGLE_MIN <= t[0] <= RADAR_SWEEP_ANGLE_MAX]
    _last_target_count = len(valid)
    if valid:
        angles = np.deg2rad([180.0 - t[0] for t in valid])
        dists = np.asarray([t[1] for t in valid], dtype=np.float64)
        x = np.ascontiguousarray(dists * np.cos(angles), dtype=np.float64)
        y = np.ascontiguousarray(dists * np.sin(angles), dtype=np.float64)
        dpg.set_value("ppi_target_series", (x, y))
    else:
        dpg.set_value("ppi_target_series", ([], []))
    _refresh_header()
