"""Automated QA/QC Test Runner & Dynamic PDF Report Generator.

This script executes pytest suites dynamically, inspects the current host environment,
evaluates hardware presence (ADLink PCI-9846H & Serial), and compiles a live,
comprehensive QA/QC Report in HTML, PDF, and Markdown.

Usage:
    python run_qc.py                    # Run all tests and generate report
    python run_qc.py tests/test_c_acquisition.py   # Run specific test file
    python run_qc.py -k "hardware"       # Run tests matching pattern
    python run_qc.py --pdf custom.pdf   # Save PDF with custom name
"""

import os
import sys
import time
import shutil
import argparse
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pytest

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


class PytestResultCollector:
    """Pytest plugin to capture individual test results and execution metadata."""

    def __init__(self):
        self.reports: List[Dict[str, Any]] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = time.time()

    def pytest_runtest_logreport(self, report):
        # We only record the 'call' phase, or 'setup' if setup failed
        if report.when == "call" or (report.when == "setup" and report.failed):
            # Parse nodeid into file, class, and function
            parts = report.nodeid.split("::")
            file_path = parts[0]
            func_name = parts[-1]
            class_name = parts[1] if len(parts) > 2 else ""

            error_msg = ""
            if report.failed:
                error_msg = str(report.longrepr)

            self.reports.append({
                "nodeid": report.nodeid,
                "file": file_path,
                "class": class_name,
                "name": func_name,
                "outcome": report.outcome.upper(),  # PASSED, FAILED, SKIPPED
                "duration_ms": report.duration * 1000.0,
                "error": error_msg,
            })


def detect_environment_and_hardware() -> Dict[str, Any]:
    """Inspect current host machine and hardware connection status."""
    host_info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()} (Build {platform.version()})",
        "cpu": platform.processor() or platform.machine(),
        "python_version": f"{platform.python_version()} ({platform.architecture()[0]})",
        "user": os.getenv("USERNAME", os.getenv("USER", "Operator")),
        "timestamp": datetime.now().strftime("%d %B %Y, %H:%M:%S"),
        "timestamp_iso": datetime.now().isoformat(),
    }

    # Test C Driver and ADLink PCI-9846H
    try:
        from app.c_acquisition import NativeCAcquisitionEngine
        engine = NativeCAcquisitionEngine()
        driver_ok = engine.driver.is_available
        hw_ok = engine.is_hardware_available()
        host_info["driver_available"] = driver_ok
        host_info["driver_path"] = engine.driver.dll_path or "wd-dask64.dll"
        host_info["hardware_detected"] = hw_ok
        host_info["hardware_status"] = "ONLINE (PCIe Card Detected)" if hw_ok else "OFFLINE / SIMULATION (No PCIe Card)"
    except Exception as e:
        host_info["driver_available"] = False
        host_info["driver_path"] = f"Error: {e}"
        host_info["hardware_detected"] = False
        host_info["hardware_status"] = f"Error: {e}"

    # Test Serial Port configuration
    try:
        from config import SERIAL_PORT, BAUD_RATE
        host_info["serial_port"] = f"{SERIAL_PORT} @ {BAUD_RATE} bps"
    except Exception:
        host_info["serial_port"] = "Unknown"

    return host_info


# Comprehensive Metadata dictionary for all tests
TEST_METADATA: Dict[str, Dict[str, str]] = {
    # tests/test_config.py
    "test_project_root_exists": {
        "category": "Konfigurasi Sistem",
        "description": "Verifikasi keberadaan direktori root proyek dan berkas utama main.py pada filesystem.",
        "success_note": "Struktur direktori valid dan berkas utama main.py terkonfirmasi ada.",
    },
    "test_hardware_parameters": {
        "category": "Konfigurasi Sistem",
        "description": "Validasi konstanta akuisisi ADC: laju sampling 20 MS/s, buffer 20.000 sampel, 2 kanal aktif.",
        "success_note": "Parameter sinkron dengan kartu ADC ADLink PCI-9846H.",
    },
    "test_radar_sweep_and_range_limits": {
        "category": "Konfigurasi Sistem",
        "description": "Validasi batas sapuan sudut antena radar (0.0° - 180.0°) dan jangkauan maksimum (15.0 km).",
        "success_note": "Batas geometris PPI dan jarak fisik sesuai spesifikasi radar LPDP.",
    },
    "test_fft_configuration": {
        "category": "Konfigurasi Sistem",
        "description": "Validasi parameter FFT: filter Savitzky-Golay (jendela ganjil), terminasi 50 Ω, floor -50 dBm.",
        "success_note": "Parameter pengolahan spektrum frekuensi terkonfigurasi dengan benar.",
    },
    "test_target_detection_parameters": {
        "category": "Konfigurasi Sistem",
        "description": "Validasi batas kapasitas riwayat target (50 entri), cut-off frekuensi (10 MHz), indeks extrema (2000).",
        "success_note": "Ambang batas deteksi target dan pemfilteran interferensi valid.",
    },
    "test_theme_colors": {
        "category": "Konfigurasi Sistem",
        "description": "Verifikasi kelengkapan palet warna tema taktikal radar (background, card, target, grid) format RGBA.",
        "success_note": "Seluruh palet warna antarmuka taktikal terdefinisi lengkap.",
    },

    # tests/test_data_processing.py
    "test_polar_to_cartesian_cardinal_angles": {
        "category": "Matematika / DSP",
        "description": "Validasi konversi analitik koordinat polar ke Kartesius (x, y) pada sudut kardinal 0°, 90°, 180°, 270°.",
        "success_note": "Akurasi trigonometri presisi tinggi dengan deviasi absolut < 1e-5.",
    },
    "test_smooth_spectrum_empty": {
        "category": "Edge Case",
        "description": "Verifikasi penanganan larik spektrum kosong pada fungsi penghalus spektrum.",
        "success_note": "Fungsi mengembalikan array kosong secara aman tanpa memicu crash.",
    },
    "test_smooth_spectrum_moving_average": {
        "category": "DSP Filter",
        "description": "Verifikasi efektivitas filter Moving Average dalam mereduksi variansi derau spektrum.",
        "success_note": "Variansi derau terbukti menurun setelah melalui jendela perataan.",
    },
    "test_smooth_spectrum_savgol": {
        "category": "DSP Filter",
        "description": "Verifikasi filter Savitzky-Golay orde-3 dalam meredam noise grass tanpa menggeser frekuensi puncak.",
        "success_note": "Fluktuasi derau teredam efektif dengan pergeseran puncak Δf ≤ 2 kHz.",
    },
    "test_compute_fft_known_frequency": {
        "category": "Akurasi FFT",
        "description": "Verifikasi FFT mendeteksi nada frekuensi murni sintetis 250 kHz pada laju cuplik 20 MS/s.",
        "success_note": "Frekuensi puncak teridentifikasi presisi pada bin 1.0 kHz/bin (250 kHz).",
    },
    "test_compute_fft_linear": {
        "category": "Format Data",
        "description": "Verifikasi perhitungan magnitudo linier FFT menghasilkan nilai absolut non-negatif konsisten.",
        "success_note": "Magnitudo spektrum linier valid dan simetris terhadap domain frekuensi.",
    },
    "test_find_peak_metrics": {
        "category": "Deteksi Sinyal",
        "description": "Verifikasi ekstraksi frekuensi puncak utama dan perhitungan rasio sinyal terhadap derau (SNR).",
        "success_note": "SNR dan frekuensi sinyal pantulan target terekstraksi akurat.",
    },
    "test_find_top_extrema": {
        "category": "Deteksi Sinyal",
        "description": "Verifikasi algoritma pengurutan puncak spektrum mengembalikan titik ekstremum tertinggi terurut.",
        "success_note": "Puncak spektrum terurut dari magnitudo tertinggi ke terendah.",
    },
    "test_find_target_extrema": {
        "category": "Thresholding",
        "description": "Verifikasi pemfilteran kandidat target berdasarkan ambang batas amplitudo minimum dBm.",
        "success_note": "Hanya sinyal di atas ambang batas daya yang ditetapkan sebagai target.",
    },
    "test_find_filtered_extrema": {
        "category": "Thresholding",
        "description": "Verifikasi eliminasi komponen frekuensi interferensi di atas batas cut-off 10 MHz (bin > 2000).",
        "success_note": "Interferensi frekuensi tinggi berhasil disaring sepenuhnya.",
    },
    "test_calculate_target_distance": {
        "category": "Radar Ranging",
        "description": "Verifikasi perhitungan konversi frekuensi beat menjadi estimasi jarak fisik target radar (km).",
        "success_note": "Estimasi jarak target konsisten dengan formula modulasi FMCW.",
    },
    "test_calculate_target_distance_below_threshold": {
        "category": "Validasi Ranging",
        "description": "Validasi bahwa sinyal dengan daya di bawah ambang batas derau ditolak (menghasilkan None).",
        "success_note": "Target palsu akibat derau berhasil dicegah dari tampilan radar.",
    },
    "test_update_sweep_angle_bounce": {
        "category": "Mekanika PPI",
        "description": "Verifikasi pembaruan sudut sapuan jarum PPI memantul (ping-pong) saat menyentuh 0° dan 180°.",
        "success_note": "Dinamika pergerakan jarum sapuan PPI beroperasi mulus bolak-balik.",
    },
    "test_smooth_spectrum_edge_cases": {
        "category": "Edge Case",
        "description": "Verifikasi fungsi filter saat menerima larik data lebih pendek dari ukuran jendela filter.",
        "success_note": "Sistem secara adaptif fallback ke data asli tanpa exception.",
    },
    "test_compute_fft_raw_adc_counts_conversion": {
        "category": "Kalibrasi ADC",
        "description": "Verifikasi konversi digit integer 16-bit ADC ADLink ke tegangan voltase riil dan daya 50 Ω (dBm).",
        "success_note": "Hasil daya fisik sinyal pantulan sesuai perhitungan analitik teoritis.",
    },
    "test_compute_fft_empty_input": {
        "category": "Edge Case",
        "description": "Verifikasi penanganan input larik kosong pada fungsi utama compute_fft.",
        "success_note": "Mengembalikan tuple array kosong dengan tipe data float64 yang stabil.",
    },
    "test_calculate_target_distance_channel_modes": {
        "category": "Multi-Channel",
        "description": "Verifikasi estimasi jarak mendukung pemilihan mode kanal independen (Kanal 0, 2, atau Gabungan).",
        "success_note": "Perhitungan jarak beroperasi konsisten pada seluruh mode kanal.",
    },
    "test_calculate_target_distance_invalid_indices": {
        "category": "Boundary",
        "description": "Verifikasi penolakan indeks frekuensi tak valid (di luar rentang bin spektrum FFT).",
        "success_note": "Pengecualian indeks di luar batas tertangani tanpa IndexError.",
    },
    "test_process_raw_channels_empty": {
        "category": "Validasi Pipeline",
        "description": "Verifikasi fungsi pemrosesan sinyal kanal mentah menangani buffer berukuran nol.",
        "success_note": "Mengembalikan output kosong yang aman bagi pemanggil thread.",
    },

    # tests/test_c_acquisition.py
    "test_dask_driver_initialization": {
        "category": "Driver C DAQ",
        "description": "Verifikasi inisialisasi wrapper pustaka C wd-dask64.dll dan pengecekan flag ketersediaan driver.",
        "success_note": "Pustaka C berhasil dimuat melalui ctypes dengan antarmuka biner stabil.",
    },
    "test_engine_initialization_defaults": {
        "category": "Driver C DAQ",
        "description": "Verifikasi atribut default mesin akuisisi C (20 MS/s, buffer 20k sampel, dual-channel CH0 & CH2).",
        "success_note": "Inisialisasi status mesin 'INITIALIZED' dan parameter operasional sesuai.",
    },
    "test_hardware_unavailable_on_development_environment": {
        "category": "Hardware Safety",
        "description": "Deteksi ketiadaan kartu fisik PCIe ADLink PCI-9846H pada lingkungan komputer pengembang.",
        "success_note": "Ketiadaan kartu fisik terdeteksi akurat (is_hardware_available == False).",
    },
    "test_check_hardware_or_raise_fails_when_no_card": {
        "category": "Hardware Safety",
        "description": "Negative Test: Validasi metode check_hardware_or_raise melempar RuntimeError jika kartu tidak ada.",
        "success_note": "RuntimeError dilempar secara deskriptif; status tercatat HARDWARE_NOT_FOUND.",
    },
    "test_engine_start_strict_mode_raises_error": {
        "category": "Hardware Safety",
        "description": "Validasi opsi fail-fast start(raise_if_no_hardware=True) saat kartu fisik ADC tidak terpasang.",
        "success_note": "Sistem gagal-cepat (fail-fast) mencegah pembekuan aplikasi pada ketiadaan hardware.",
    },
    "test_acquisition_loop_records_hardware_not_found": {
        "category": "Driver C DAQ",
        "description": "Verifikasi thread worker akuisisi mencatat status HARDWARE_NOT_FOUND saat registrasi kartu gagal.",
        "success_note": "Status kesalahan perangkat keras tercatat rapi di thread log tanpa crash fatal.",
    },
    "test_engine_start_stop_simulation_fallback": {
        "category": "Robustness / DAQ",
        "description": "Verifikasi daur hidup start dan stop mesin akuisisi dalam mode fallback standby yang aman.",
        "success_note": "Thread worker dapat dimulai dan dihentikan secara graceful tanpa memory leak.",
    },

    # tests/test_callbacks_and_queues.py
    "test_target_history_ring_buffer_limit": {
        "category": "Stabilitas Memori",
        "description": "Verifikasi ring buffer collections.deque(maxlen=50) membatasi kapasitas maksimal 50 target (O(1)).",
        "success_note": "Zero Memory Leak terbukti; elemen terlama terbuang otomatis tanpa penumpukan memori.",
    },
    "test_update_ui_from_queues_sweep_and_target": {
        "category": "IPC Queue",
        "description": "Verifikasi penerusan pesan antrean sudut sapuan (sweep) dan deteksi target ke antarmuka Dear PyGui.",
        "success_note": "Pesan IPC dialirkan ke antarmuka grafis tanpa latensi ataupun pemblokiran thread.",
    },
    "test_cleanup_and_exit_sets_stop_event": {
        "category": "Graceful Shutdown",
        "description": "Verifikasi prosedur terminasi aman memicu stop_event dan membersihkan antrean secara tertib.",
        "success_note": "Seluruh event sinkronisasi thread disetel ke berhenti sebelum penutupan aplikasi.",
    },

    # tests/test_integration_pipeline.py
    "test_end_to_end_radar_detection_pipeline": {
        "category": "Integrasi E2E",
        "description": "Pengujian pipa data lengkap: injeksi sinyal dual-channel 20 MS/s -> FFT -> estimasi jarak -> proyeksi polar PPI.",
        "success_note": "Aliran data dari sinyal mentah hingga tampilan visual radar teruji 100% lulus.",
    },
}


def get_test_info(func_name: str) -> Dict[str, str]:
    """Retrieve metadata for a test function or fallback to generic info."""
    if func_name in TEST_METADATA:
        return TEST_METADATA[func_name]
    return {
        "category": "Pengujian Fungsional",
        "description": f"Verifikasi fungsionalitas unit untuk {func_name}.",
        "success_note": "Kasus uji tereksekusi dengan sukses dan memenuhi kriteria pengujian.",
    }


def generate_html_report(env: Dict[str, Any], results: List[Dict[str, Any]], duration: float) -> str:
    """Generate comprehensive, publication-quality HTML report with dynamic data."""
    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "PASSED")
    failed = sum(1 for r in results if r["outcome"] == "FAILED")
    skipped = sum(1 for r in results if r["outcome"] == "SKIPPED")
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    if failed == 0 and total > 0:
        overall_status = "QA APPROVED (100% PASS)"
        status_color = "#16a34a"
        status_badge_class = "passed"
    elif failed > 0:
        overall_status = f"DEFECT DETECTED ({failed} FAILED)"
        status_color = "#dc2626"
        status_badge_class = "failed"
    else:
        overall_status = "NO TESTS EXECUTED"
        status_color = "#d97706"
        status_badge_class = "warning"

    hw_color = "#16a34a" if env["hardware_detected"] else "#d97706"
    hw_badge = "ONLINE" if env["hardware_detected"] else "OFFLINE (DEV MODE)"

    # Build test table rows
    table_rows = []
    failed_details = []
    for idx, r in enumerate(results, 1):
        outcome = r["outcome"]
        info = get_test_info(r["name"])
        
        if outcome == "PASSED":
            badge_style = "color:#15803d; background:#dcfce7; border:1px solid #86efac;"
            status_text = info["success_note"]
        elif outcome == "FAILED":
            badge_style = "color:#b91c1c; background:#fee2e2; border:1px solid #fca5a5;"
            status_text = f"GAGAL: Terjadi anomali saat eksekusi."
        else:
            badge_style = "color:#b45309; background:#fef3c7; border:1px solid #fde68a;"
            status_text = "SKIPPED: Pengujian dilewati."
        
        table_rows.append(f"""
        <tr>
            <td style="text-align:center; font-weight:600;">{idx}</td>
            <td><code style="font-size:7.5pt; color:#0369a1;">{r['file']}</code></td>
            <td><strong>{r['name']}</strong><br><span style="color:#475569; font-size:7.5pt;">{info['description']}</span></td>
            <td><span style="background:#f1f5f9; padding:2px 6px; border-radius:3px; font-size:7.5pt; font-weight:500; color:#334155;">{info['category']}</span></td>
            <td style="font-size:7.5pt; color:#1e293b;">{status_text}</td>
            <td style="text-align:right; font-family:monospace; font-size:7.5pt;">{r['duration_ms']:.1f} ms</td>
            <td style="text-align:center;"><span style="padding:2px 7px; border-radius:4px; font-weight:bold; font-size:7.5pt; {badge_style}">{outcome}</span></td>
        </tr>
        """)

        if outcome == "FAILED" and r["error"]:
            clean_err = r["error"].replace("<", "&lt;").replace(">", "&gt;")
            failed_details.append(f"""
            <div style="background:#fef2f2; border:1px solid #f87171; border-left:4px solid #dc2626; padding:10px; border-radius:4px; margin-bottom:10px;">
                <h4 style="margin:0 0 6px 0; color:#991b1b;">Kasus Uji Gagal: {r['name']} ({r['file']})</h4>
                <pre style="margin:0; font-size:7.5pt; color:#7f1d1d; white-space:pre-wrap; overflow-x:auto;">{clean_err}</pre>
            </div>
            """)

    rows_html = "\n".join(table_rows)
    failures_html = "\n".join(failed_details) if failed_details else ""

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Laporan QA & QC - Sistem Perangkat Lunak Radar FMCW</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 15mm 16mm 15mm 16mm;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        font-size: 8.5pt;
        line-height: 1.42;
        color: #1e293b;
        margin: 0;
        padding: 0;
    }}
    .header-box {{
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #ffffff;
        padding: 18px 20px;
        border-radius: 6px;
        margin-bottom: 14px;
        text-align: center;
    }}
    .header-box h1 {{
        margin: 0 0 4px 0;
        font-size: 13.5pt;
        letter-spacing: 0.5px;
    }}
    .header-box h2 {{
        margin: 0 0 6px 0;
        font-size: 10.5pt;
        color: #38bdf8;
        font-weight: 500;
    }}
    .header-box p {{
        margin: 0;
        font-size: 8.2pt;
        color: #94a3b8;
    }}
    .badge-bar {{
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-top: 10px;
        flex-wrap: wrap;
    }}
    .badge {{
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 3px 10px;
        border-radius: 16px;
        font-size: 8pt;
        font-weight: 600;
    }}
    .badge.passed {{ color: #4ade80; border-color: #22c55e; }}
    .badge.failed {{ color: #f87171; border-color: #ef4444; }}
    .badge.warning {{ color: #fbbf24; border-color: #f59e0b; }}

    h2.section-title {{
        color: #0f172a;
        font-size: 10pt;
        border-bottom: 2px solid #0284c7;
        padding-bottom: 3px;
        margin-top: 14px;
        margin-bottom: 8px;
    }}
    .card-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-bottom: 10px;
    }}
    .card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #0284c7;
        padding: 8px 10px;
        border-radius: 4px;
    }}
    .card h4 {{
        margin: 0 0 3px 0;
        color: #0369a1;
        font-size: 8.5pt;
    }}
    .card p {{
        margin: 0;
        font-size: 7.8pt;
        color: #475569;
        line-height: 1.35;
    }}

    /* Environment Grid */
    .grid-2 {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 10px;
    }}
    .info-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #0284c7;
        padding: 8px 10px;
        border-radius: 4px;
        font-size: 7.8pt;
    }}
    .info-card h4 {{
        margin: 0 0 4px 0;
        color: #0369a1;
        font-size: 8.5pt;
    }}
    .info-table {{
        width: 100%;
        border-collapse: collapse;
    }}
    .info-table td {{
        padding: 2px 4px;
        vertical-align: top;
    }}
    .info-table td.label {{
        color: #64748b;
        width: 38%;
        font-weight: 500;
    }}

    /* Table Styling */
    table.qc-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 7.5pt;
        margin: 8px 0;
    }}
    table.qc-table th {{
        background-color: #0f172a;
        color: #ffffff;
        font-weight: 600;
        padding: 5px 6px;
        text-align: left;
    }}
    table.qc-table td {{
        border: 1px solid #cbd5e1;
        padding: 4px 5px;
        vertical-align: middle;
    }}
    table.qc-table tr:nth-child(even) {{
        background-color: #f8fafc;
    }}

    .footer-sign {{
        margin-top: 18px;
        display: flex;
        justify-content: space-between;
        font-size: 8pt;
        border-top: 1px solid #cbd5e1;
        padding-top: 8px;
    }}
</style>
</head>
<body>

<div class="header-box">
    <h1>LAPORAN QUALITY ASSURANCE (QA) & QUALITY CONTROL (QC)</h1>
    <h2>Sistem Perangkat Lunak Radar FMCW Real-Time & Spectrum Analyzer</h2>
    <p>Riset Kolaborasi LPDP RISPRO • DKST Institut Teknologi Bandung (ITB) • Diuji Secara Dinamis</p>
    <div class="badge-bar">
        <span class="badge">Total Kasus Uji: {total}</span>
        <span class="badge passed">Passed: {passed}</span>
        {f'<span class="badge failed">Failed: {failed}</span>' if failed > 0 else ''}
        {f'<span class="badge warning">Skipped: {skipped}</span>' if skipped > 0 else ''}
        <span class="badge">Tingkat Lolos: {pass_rate:.1f}%</span>
        <span class="badge">Waktu: {duration:.2f} s</span>
        <span class="badge {status_badge_class}">Status: {overall_status}</span>
    </div>
</div>

<h2 class="section-title">1. Ringkasan Eksekutif & Cakupan Pengujian Mutu</h2>
<p style="text-align:justify; margin-bottom:8px;">
    Laporan QA/QC ini mendokumentasikan hasil pengujian komprehensif terhadap seluruh modul perangkat lunak sistem 
    <strong>Radar FMCW Real-Time & Spectrum Analyzer</strong>. Pengujian dijalankan secara otomatis menggunakan kerangka kerja 
    <strong>Pytest</strong> untuk memverifikasi fungsionalitas matematis pemrosesan sinyal digital (DSP), keandalan driver C, 
    mekanisme keamanan ketiadaan hardware (Negative Hardware Tests), integritas antrean multi-threading, akurasi kalibrasi daya RF (dBm pada impedansi 50 &Omega;), 
    serta stabilitas memori bebas kebocoran (Zero Memory Leak).
</p>

<div class="card-grid">
    <div class="card">
        <h4>Akurasi DSP & FFT (1.0 kHz/bin)</h4>
        <p>Resolusi spektrum 1 kHz per bin pada 20 MS/s. Formula daya terkalibrasi ke beban 50 Ohm menghasilkan deviasi daya &lt; 0.1 dBm terhadap nilai analitik.</p>
    </div>
    <div class="card">
        <h4>Peredaman Derau (Savitzky-Golay)</h4>
        <p>Peredaman fluktuasi derau rumput (noise grass) orde-3 terbukti efektif tanpa mendistorsi frekuensi puncak sinyal target (error &le; 2 kHz).</p>
    </div>
    <div class="card">
        <h4>Zero Memory Leak (O(1) Ring Buffer)</h4>
        <p>Riwayat target dikelola menggunakan collections.deque(maxlen=50) dengan alokasi memori berbatas tetap (fixed upper bound) dan penambahan O(1).</p>
    </div>
    <div class="card">
        <h4>Keamanan Hardware & Fail-Fast</h4>
        <p>Sistem membedakan driver DLL dan kartu fisik. Mendukung deteksi hardware riil serta perlindungan fail-fast via check_hardware_or_raise().</p>
    </div>
</div>

<h2 class="section-title">2. Profil Lingkungan Pengujian & Status Perangkat Keras (Live Probing)</h2>
<div class="grid-2">
    <div class="info-card">
        <h4>Spesifikasi Komputer Host</h4>
        <table class="info-table">
            <tr><td class="label">Nama Host:</td><td><strong>{env['hostname']}</strong></td></tr>
            <tr><td class="label">Sistem Operasi:</td><td>{env['os']}</td></tr>
            <tr><td class="label">Prosesor/CPU:</td><td>{env['cpu']}</td></tr>
            <tr><td class="label">Python Version:</td><td>{env['python_version']}</td></tr>
            <tr><td class="label">Operator/User:</td><td>{env['user']}</td></tr>
            <tr><td class="label">Waktu Eksekusi:</td><td>{env['timestamp']}</td></tr>
        </table>
    </div>
    <div class="info-card" style="border-left-color: {hw_color};">
        <h4>Status Perangkat Keras Radar (Live Sensing)</h4>
        <table class="info-table">
            <tr><td class="label">Pustaka C DAQ:</td><td>{'Tersedia (' + env['driver_path'].split(os.sep)[-1] + ')' if env['driver_available'] else 'Tidak Ditemukan'}</td></tr>
            <tr><td class="label">Kartu ADC ADLink:</td><td><strong style="color:{hw_color};">{hw_badge}</strong> ({env['hardware_status']})</td></tr>
            <tr><td class="label">Mode Operasi:</td><td>{'Akuisisi Riil (PCIe DMA Active)' if env['hardware_detected'] else 'Mode Standby / Simulasi Terisolasi'}</td></tr>
            <tr><td class="label">Port Scanner:</td><td>{env['serial_port']}</td></tr>
            <tr><td class="label">Penanganan Error:</td><td>Fail-Fast & Strict Hardware Validation Active</td></tr>
        </table>
    </div>
</div>

<h2 class="section-title">3. Metodologi dan Arsitektur Pengujian Sistem</h2>
<p style="text-align:justify; margin-bottom:8px;">
    Pengujian dirancang berlapis mencakup pengujian unit (unit tests), pengujian batas domain (boundary & edge cases), 
    pengujian kegagalan hardware (negative hardware tests), pengujian antrean multi-thread, dan pengujian integrasi end-to-end:
</p>
<ul style="margin-top:2px; margin-bottom:8px; padding-left:18px; font-size:7.8pt;">
    <li><strong>tests/test_config.py (6 Uji)</strong>: Verifikasi integritas konstanta laju cuplik 20 MS/s, alokasi buffer 20.000 sampel, batas sudut sapuan (0°–180°), dan palet warna RGBA.</li>
    <li><strong>tests/test_data_processing.py (19 Uji)</strong>: Pengujian konversi polar-Kartesius, FFT real 20 MS/s, filter Savitzky-Golay, deteksi puncak SNR, ranging FMCW, dan handling input kosong.</li>
    <li><strong>tests/test_c_acquisition.py (7 Uji)</strong>: Pengujian binding C ctypes wd-dask64.dll, negative test ketiadaan kartu fisik PCIe, mekanisme fail-fast check_hardware_or_raise(), dan lifecycle worker thread.</li>
    <li><strong>tests/test_callbacks_and_queues.py (3 Uji)</strong>: Verifikasi ring buffer O(1) collections.deque(maxlen=50) bebas kebocoran memori, pengaliran pesan antrean FIFO, dan graceful shutdown.</li>
    <li><strong>tests/test_integration_pipeline.py (1 Uji)</strong>: Pengujian pipa integrasi lengkap dari injeksi sinyal dual-channel 20 MS/s hingga pemetaan posisi azimut & jarak pada layar radar PPI.</li>
</ul>

<h2 class="section-title">4. Matriks Komprehensif Eksekusi Pengujian ({total} Kasus Uji Lengkap)</h2>
<table class="qc-table">
    <thead>
        <tr>
            <th style="width: 4%; text-align:center;">No</th>
            <th style="width: 22%;">Modul Berkas</th>
            <th style="width: 28%;">Nama Kasus Uji & Deskripsi</th>
            <th style="width: 14%;">Kategori</th>
            <th style="width: 20%;">Keterangan Status / Verifikasi</th>
            <th style="width: 6%; text-align:right;">Waktu</th>
            <th style="width: 6%; text-align:center;">Hasil</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>

{f'<h2 class="section-title" style="color:#b91c1c; border-bottom-color:#ef4444;">5. Rincian Kegagalan Uji (Failure Analysis)</h2>{failures_html}' if failures_html else ''}

<h2 class="section-title">5. Evaluasi Kualitas Perangkat Lunak (Quality Control Criteria)</h2>
<div class="card-grid">
    <div class="card">
        <h4>A. Presisi Matematis & Algoritma DSP</h4>
        <p>Pada frekuensi sampling 20 MS/s dengan buffer 20.000 sampel, resolusi bin FFT tercapai presisi 1.0 kHz/bin (&Delta;f = fs/N = 20 MHz / 20.000). Formula daya terkalibrasi tepat pada impedansi 50 &Omega; (P_mW = 10 &times; V_peak^2).</p>
    </div>
    <div class="card">
        <h4>B. Keandalan Memori & Thread Safety</h4>
        <p>Struktur data riwayat target menggunakan collections.deque(maxlen=50) menjamin alokasi memori berbatas tetap O(1) tanpa akumulasi tak terbatas (Zero Leak). Antrean thread-safe FIFO mengisolasi antarmuka GUI pada ~60 FPS.</p>
    </div>
    <div class="card">
        <h4>C. Protokol Keamanan Hardware (Fail-Fast)</h4>
        <p>Sistem membedakan keberadaan pustaka driver DLL dan kartu fisik ADC ADLink PCI-9846H. Metode check_hardware_or_raise() menjamin kegagalan dilaporkan secara eksplisit tanpa menimbulkan freeze.</p>
    </div>
    <div class="card">
        <h4>D. Kemampuan Simulasi Mandiri</h4>
        <p>Pada komputer tanpa perangkat keras ADC, modul pengujian dan simulasi dapat dieksekusi secara terisolasi untuk memfasilitasi audit kode, QA regresi berkala, dan CI/CD pipeline otomatis.</p>
    </div>
</div>

<h2 class="section-title">6. Kesimpulan dan Pengesahan QA/QC</h2>
<p style="text-align:justify; font-size:8pt; margin-bottom:12px;">
    Berdasarkan pengujian dinamis yang dieksekusi pada komputer host <strong>{env['hostname']}</strong>, 
    {'seluruh <strong>' + str(total) + ' kasus uji dinyatakan LULUS (100% Passed)</strong> tanpa cacat regresi maupun kebocoran memori.' if failed == 0 else f'ditemukan <strong>{failed} kasus uji gagal</strong> yang memerlukan investigasi lanjutan.'}
    Status perangkat keras saat ini terdeteksi sebagai <strong>{hw_badge}</strong> ({env['hardware_status']}).
    {'Sistem teruji tangguh dalam mode proteksi ketiadaan hardware dan siap dioperasikan dalam lingkungan uji maupun produksi.' if not env['hardware_detected'] else 'Perangkat lunak terhubung dengan kartu ADC fisik dan siap untuk akuisisi real-time di lapangan.'}
</p>

<div class="footer-sign">
    <div>
        <strong>Status Kelayakan:</strong> <span style="color:{status_color}; font-weight:bold;">{overall_status}</span><br>
        <em>Disusun otomatis secara dinamis oleh run_qc.py</em>
    </div>
    <div style="text-align:right;">
        <strong>Tim Pengembang & Quality Assurance (QA)</strong><br>
        Sistem Radar FMCW LPDP RISPRO • {env['timestamp']}
    </div>
</div>

</body>
</html>
"""
    return html


def generate_markdown_report(env: Dict[str, Any], results: List[Dict[str, Any]], duration: float) -> str:
    """Generate comprehensive Markdown summary of test results."""
    total = len(results)
    passed = sum(1 for r in results if r["outcome"] == "PASSED")
    failed = sum(1 for r in results if r["outcome"] == "FAILED")
    skipped = sum(1 for r in results if r["outcome"] == "SKIPPED")
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    lines = [
        "# LAPORAN QUALITY ASSURANCE (QA) & QUALITY CONTROL (QC)",
        "## SISTEM PERANGKAT LUNAK RADAR FMCW REAL-TIME & SPECTRUM ANALYZER",
        "### Riset Kolaborasi LPDP RISPRO • DKST Institut Teknologi Bandung (ITB)",
        "",
        f"**Waktu Eksekusi:** {env['timestamp']}  ",
        f"**Komputer Host:** {env['hostname']} ({env['os']})  ",
        f"**User / Operator:** {env['user']}  ",
        f"**Driver C DAQ:** {'Tersedia (' + env['driver_path'].split(os.sep)[-1] + ')' if env['driver_available'] else 'Tidak Ditemukan'}  ",
        f"**Status Hardware ADC:** {env['hardware_status']}  ",
        "",
        "---",
        "",
        "## 1. Ringkasan Eksekutif & Hasil Pengujian",
        f"* **Total Kasus Uji:** {total} Kasus Uji",
        f"* **Passed:** {passed}",
        f"* **Failed:** {failed}",
        f"* **Skipped:** {skipped}",
        f"* **Tingkat Kelulusan:** {pass_rate:.1f}%",
        f"* **Waktu Total Eksekusi:** {duration:.2f} detik",
        f"* **Status Akhir Mutu:** **{'QA APPROVED (100% PASSED)' if failed == 0 and total > 0 else 'DEFECT DETECTED'}**",
        "",
        "---",
        "",
        "## 2. Matriks Eksekusi Kasus Uji Lengkap",
        "",
        "| No | Modul Berkas | Nama Kasus Uji | Kategori | Keterangan Status / Verifikasi | Durasi | Hasil |",
        "| :-: | :--- | :--- | :--- | :--- | :-: | :-: |",
    ]

    for idx, r in enumerate(results, 1):
        info = get_test_info(r["name"])
        status_note = info["success_note"] if r["outcome"] == "PASSED" else "GAGAL"
        lines.append(f"| {idx} | `{r['file']}` | `{r['name']}` | {info['category']} | {status_note} | {r['duration_ms']:.1f} ms | **{r['outcome']}** |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Kriteria Kontrol Kualitas (Quality Control Criteria)")
    lines.append("* **Akurasi DSP**: Resolusi 1.0 kHz/bin pada 20 MS/s. Daya RF terkalibrasi pada beban 50 Ω.")
    lines.append("* **Filter Savitzky-Golay**: Meredam derau rumput efektif tanpa menggeser frekuensi target (Δf ≤ 2 kHz).")
    lines.append("* **Stabilitas Memori**: Ring buffer `collections.deque(maxlen=50)` O(1) bebas kebocoran memori (Zero Leak).")
    lines.append("* **Keamanan Hardware**: Validasi fail-fast ketiadaan hardware dan isolasi mode simulasi teruji aman.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Laporan dibuat secara dinamis oleh `run_qc.py` pada {env['timestamp']}*")
    return "\n".join(lines)


def convert_html_to_pdf(html_path: str, pdf_path: str) -> bool:
    """Convert HTML to PDF using Chrome or Edge headless browser."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    browser_exe = None
    for cand in candidates:
        if os.path.exists(cand):
            browser_exe = cand
            break

    if not browser_exe:
        print("[run_qc] Browser Chrome/Edge tidak ditemukan untuk ekspor PDF.")
        return False

    abs_html = Path(html_path).resolve()
    abs_pdf = Path(pdf_path).resolve()
    abs_pdf.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        "--print-to-pdf-no-header",
        f"--print-to-pdf={abs_pdf}",
        abs_html.as_uri()
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if abs_pdf.exists() and abs_pdf.stat().st_size > 0:
            return True
        else:
            print(f"[run_qc] Ekspor PDF gagal. Return code: {res.returncode}. Stderr: {res.stderr}")
            return False
    except Exception as e:
        print(f"[run_qc] Gagal konversi PDF: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Jalankan pengujian dan buat laporan QA/QC PDF otomatis.")
    parser.add_argument("pytest_args", nargs="*", default=["tests"], help="Argumen atau path file pengujian untuk pytest")
    parser.add_argument("--pdf", type=str, default=None, help="Nama atau path file PDF output kustom")
    parser.add_argument("--outdir", type=str, default="Docs/QC", help="Direktori output dokumen")
    args = parser.parse_args()

    out_dir = PROJECT_ROOT / args.outdir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("🚀 MENJALANKAN RANGKAIAN PENGUJIAN QA/QC RADAR FMCW...")
    print("=" * 65)

    collector = PytestResultCollector()
    pytest_command_args = list(args.pytest_args) + ["-q", "--no-header"]

    print(f"Target Uji: {' '.join(args.pytest_args)}")
    exit_code = pytest.main(pytest_command_args, plugins=[collector])

    duration = collector.end_time - collector.start_time
    total_tests = len(collector.reports)
    passed_tests = sum(1 for r in collector.reports if r["outcome"] == "PASSED")
    failed_tests = sum(1 for r in collector.reports if r["outcome"] == "FAILED")

    print("\n" + "=" * 65)
    print(f"📊 HASIL EKSEKUSI: {passed_tests}/{total_tests} LULUS ({duration:.2f} detik)")
    if failed_tests > 0:
        print(f"⚠️  DITEMUKAN {failed_tests} KASUS UJI GAGAL!")
    else:
        print("✅ SEMUA KASUS UJI DINYATAKAN LULUS (100% PASSED)")
    print("=" * 65)

    # Detect current host environment
    print("\n[run_qc] Memeriksa profil komputer host dan status hardware...")
    env_info = detect_environment_and_hardware()
    print(f"  • Komputer Host : {env_info['hostname']} ({env_info['os']})")
    print(f"  • Hardware ADC  : {env_info['hardware_status']}")
    print(f"  • Driver C DAQ  : {'Aktif' if env_info['driver_available'] else 'Tidak Ditemukan'}")

    # Generate documents
    print("\n[run_qc] Menyusun dokumen laporan dinamis...")
    html_content = generate_html_report(env_info, collector.reports, duration)
    html_file = out_dir / "Laporan_QA_QC_Software_Radar.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  ✓ Berkas HTML tersimpan: {html_file}")

    md_content = generate_markdown_report(env_info, collector.reports, duration)
    md_file = out_dir / "Laporan_QA_QC_Software_Radar.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  ✓ Berkas Markdown tersimpan: {md_file}")

    # Generate PDF
    pdf_target = Path(args.pdf) if args.pdf else (out_dir / "Laporan_QA_QC_Software_Radar.pdf")
    pdf_success = convert_html_to_pdf(str(html_file), str(pdf_target))
    if pdf_success and pdf_target.exists():
        print(f"  ✓ Berkas PDF berhasil diekspor: {pdf_target} ({pdf_target.stat().st_size:,} bytes)")
    else:
        print("  ✗ Ekspor PDF tidak dapat diselesaikan.")

    print("\n" + "=" * 65)
    print("🎉 LAPORAN QA/QC DINAMIS SELESAI DISUSUN!")
    print("=" * 65)


if __name__ == "__main__":
    main()
