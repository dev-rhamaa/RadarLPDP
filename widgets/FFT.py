"""FFT spectrum display widget.

This module provides the FFT spectrum analyzer display for both channels.
"""

import os

import dearpygui.dearpygui as dpg

from config import FILENAME, TARGET_FREQ_THRESHOLD_KHZ

# --- Fungsi Pembuat Widget UI --- #

def create_fft_widget(parent, width, height):
    """Membuat widget UI untuk menampilkan FFT Spectrum."""
    with dpg.group(parent=parent):
        dpg.add_text("Streaming DAQ Hardware PCI-9846H (In-Memory)...", tag="fft_status_text")
        
        with dpg.plot(label="Live FFT Spectrum", height=height, width=width, tag="fft_plot"):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (kHz)", tag="fft_xaxis")
            dpg.set_axis_limits("fft_xaxis", 0, TARGET_FREQ_THRESHOLD_KHZ)
            dpg.add_plot_axis(dpg.mvYAxis, label="Magnitude (dB)", tag="fft_yaxis")
            dpg.add_line_series([], [], label="CH1", parent="fft_yaxis", tag="fft_ch1_series")
            dpg.add_line_series([], [], label="CH2", parent="fft_yaxis", tag="fft_ch2_series")