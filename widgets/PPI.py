"""PPI (Plan Position Indicator) widget for radar display.

This module provides the radar PPI display with sweep line and target plotting.
"""

import math

import dearpygui.dearpygui as dpg
import numpy as np

from config import RADAR_MAX_RANGE, THEME_COLORS
from functions.data_processing import polar_to_cartesian

# --- Helper Khusus UI --- #

def generate_arc_points(center, radius, start_deg, end_deg, segments=100):
    """Menghasilkan titik-titik untuk menggambar busur."""
    points = []
    start_rad, end_rad = math.radians(start_deg), math.radians(end_deg)
    for i in range(segments + 1):
        angle = start_rad + (end_rad - start_rad) * i / segments
        points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
    return points

# --- Fungsi Pembuat Widget UI --- #

def create_ppi_widget(parent, width, height):
    """Membuat widget PPI dengan skala, lingkaran jarak, dan series untuk data."""
    with dpg.child_window(parent=parent, width=width, height=height, no_scrollbar=True):
        dpg.add_text("Plan Position Indicator (PPI) - Jarak (km)")
        
        axis_limit = int(RADAR_MAX_RANGE)
        
        with dpg.plot(label="PPI Display", width=-1, height=-1, equal_aspects=True):
            dpg.add_plot_legend()
            
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="", no_tick_labels=True, lock_min=True, lock_max=True)
            dpg.set_axis_limits(x_axis, -axis_limit, axis_limit)
            
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="", no_tick_labels=True, lock_min=True, lock_max=True)
            dpg.set_axis_limits(y_axis, 0, axis_limit) # Batas Y dari 0 hingga 15

            # Menggambar busur jarak 180 derajat (range rings)
            for r in range(3, axis_limit + 1, 3):
                theta = np.linspace(0, np.pi, 100) # 0 hingga pi untuk 180 derajat
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                dpg.add_line_series(list(x), list(y), parent=y_axis, label=f"{r} km")

            # Garis untuk sapuan radar (akan diupdate)
            dpg.add_line_series([0], [0], label="Sweep", tag="ppi_sweep_line", parent=y_axis)
            
            # Titik untuk target (akan diupdate)
                        # Titik untuk target (akan diupdate)
            dpg.add_scatter_series([], [], label="Targets", tag="ppi_target_series", parent=y_axis)

def update_sweep_line(angle):
    """Hanya memperbarui posisi garis sapuan."""
    if dpg.does_item_exist("ppi_sweep_line"):
        angle_rad = np.deg2rad(angle)
        x_end = RADAR_MAX_RANGE * np.cos(angle_rad)
        y_end = RADAR_MAX_RANGE * np.sin(angle_rad)
        dpg.set_value("ppi_sweep_line", ([0, x_end], [0, y_end]))

def add_target_to_plot(targets):
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
