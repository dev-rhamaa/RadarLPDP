# LAPORAN QUALITY ASSURANCE (QA) & QUALITY CONTROL (QC)
## SISTEM PERANGKAT LUNAK RADAR FMCW LPDP RISPRO
### Pengujian Unit, Pengujian Integrasi, dan Verifikasi Algoritma DSP

---

## 1. Ringkasan Eksekutif (Executive Summary)

Laporan Quality Assurance (QA) dan Quality Control (QC) ini mendokumentasikan hasil pengujian komprehensif terhadap seluruh modul perangkat lunak sistem **Radar FMCW Real-Time & Spectrum Analyzer** yang dikembangkan dalam kerangka riset LPDP RISPRO / DKST ITB.

Pengujian dilakukan menggunakan kerangka kerja pengujian standar industri **`pytest`** dan **`pytest-cov`**, mencakup pengujian unit (*unit testing*), pengujian batas domain (*boundary & edge cases*), pengujian integrasi pipa data (*end-to-end integration testing*), serta pengujian stabilitas memori dan performa komputasi waktu-nyata (*real-time processing*).

### Rangkuman Hasil Pengujian:
* **Total Kasus Uji (Test Cases)**: 32 Kasus Uji
* **Tingkat Kelulusan (Pass Rate)**: **100% (32 PASSED, 0 FAILED)**
* **Waktu Eksekusi**: 1.96 detik
* **Status Kualitas**: **MEMENUHI SYARAT KELAYAKAN (PRODUCTION-READY / QA APPROVED)**

---

## 2. Metodologi dan Arsitektur Pengujian

Sistem pengujian perangkat lunak dirancang dengan memisahkan pengujian ke dalam 5 modul suite uji:

1. **`tests/test_config.py` (Parameter & Konfigurasi Sistem)**:
   Verifikasi integritas konstanta sistem, batasan frekuensi sampling 20 MS/s, alokasi ukuran buffer 20.000 sampel, batas sapuan radar (0° - 180°), jarak maksimum (15 km), parameter peredaman derau FFT, serta konsistensi palet warna tema taktikal.
2. **`tests/test_data_processing.py` (Inti Pengolahan Sinyal Digital / DSP)**:
   Pengujian matematis konversi koordinat polar ke Kartesius, algoritma windowing Hann dengan normalisasi *gain* koheren, perhitungan *real* FFT, kalibrasi daya RF terukur (dBm pada impedansi 50 $\Omega$), algoritma penghalus spektrum *Savitzky-Golay*, algoritma ekstraksi puncak target, pemfilteran frekuensi >10 MHz, pemetaan jarak target (*ranging*), dan dinamika pantulan sudut jarum *sweep* PPI (0°–180°).
3. **`tests/test_c_acquisition.py` (Driver C & Mesin Akuisisi DMA)**:
   Pengujian inisialisasi pustaka tingkat rendah `wd-dask64.dll`, pemetaan tipe data C melalui `ctypes`, penanganan *asynchronous continuous restart buffer*, serta mekanisme *fallback* simulasi yang aman saat kartu perangkat keras fisik tidak terpasang.
4. **`tests/test_callbacks_and_queues.py` (Antrean Antar-Thread & UI Callbacks)**:
   Verifikasi struktur data riwayat target menggunakan ring buffer `collections.deque(maxlen=50)` dengan jaminan kompleksitas waktu $O(1)$ untuk mencegah kebocoran memori (*memory leak*), pengaliran pesan antrean *sweep* dan *target* ke antarmuka, serta prosedur terminasi aman (*graceful shutdown*).
5. **`tests/test_integration_pipeline.py` (Pengujian Pipa Integrasi End-to-End)**:
   Pengujian alur data lengkap dari masukan sinyal gelombang mikro mentah sintetis (2 kanal CH0 & CH2 pada 20 MS/s) melalui pemrosesan sinyal FFT, ekstraksi frekuensi beat, estimasi jarak target, hingga pemetaan posisi azimut dan jarak ke bidang koordinat PPI.

---

## 3. Matriks Hasil Pengujian (Test Execution Matrix)

| No | Modul Uji | Nama Kasus Uji (*Test Case*) | Kategori | Hasil |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `test_config` | `test_project_root_exists` | Konfigurasi | **PASSED** |
| 2 | `test_config` | `test_hardware_parameters` | Konfigurasi | **PASSED** |
| 3 | `test_config` | `test_radar_sweep_and_range_limits` | Konfigurasi | **PASSED** |
| 4 | `test_config` | `test_fft_configuration` | Konfigurasi | **PASSED** |
| 5 | `test_config` | `test_target_detection_parameters` | Konfigurasi | **PASSED** |
| 6 | `test_config` | `test_theme_colors` | Konfigurasi | **PASSED** |
| 7 | `test_data_processing` | `test_polar_to_cartesian_cardinal_angles` | Matematika / DSP | **PASSED** |
| 8 | `test_data_processing` | `test_smooth_spectrum_empty` | *Edge Case* | **PASSED** |
| 9 | `test_data_processing` | `test_smooth_spectrum_moving_average` | DSP Filter | **PASSED** |
| 10 | `test_data_processing` | `test_smooth_spectrum_savgol` | DSP Filter | **PASSED** |
| 11 | `test_data_processing` | `test_compute_fft_known_frequency` | Akurasi FFT | **PASSED** |
| 12 | `test_data_processing` | `test_compute_fft_linear` | Format Data | **PASSED** |
| 13 | `test_data_processing` | `test_find_peak_metrics` | Deteksi Sinyal | **PASSED** |
| 14 | `test_data_processing` | `test_find_top_extrema` | Deteksi Sinyal | **PASSED** |
| 15 | `test_data_processing` | `test_find_target_extrema` | *Thresholding* | **PASSED** |
| 16 | `test_data_processing` | `test_find_filtered_extrema` | *Thresholding* | **PASSED** |
| 17 | `test_data_processing` | `test_calculate_target_distance` | *Radar Ranging* | **PASSED** |
| 18 | `test_data_processing` | `test_calculate_target_distance_below_threshold` | *Validation* | **PASSED** |
| 19 | `test_data_processing` | `test_update_sweep_angle_bounce` | Mekanika PPI | **PASSED** |
| 20 | `test_data_processing` | `test_smooth_spectrum_edge_cases` | *Edge Case* | **PASSED** |
| 21 | `test_data_processing` | `test_compute_fft_raw_adc_counts_conversion` | Kalibrasi ADC | **PASSED** |
| 22 | `test_data_processing` | `test_compute_fft_empty_input` | *Edge Case* | **PASSED** |
| 23 | `test_data_processing` | `test_calculate_target_distance_channel_modes` | *Multi-Channel* | **PASSED** |
| 24 | `test_data_processing` | `test_calculate_target_distance_invalid_indices` | *Boundary* | **PASSED** |
| 25 | `test_data_processing` | `test_process_raw_channels_empty` | *Validation* | **PASSED** |
| 26 | `test_c_acquisition` | `test_dask_driver_initialization` | Driver DAQ | **PASSED** |
| 27 | `test_c_acquisition` | `test_engine_initialization_defaults` | Driver DAQ | **PASSED** |
| 28 | `test_c_acquisition` | `test_engine_start_stop_simulation_fallback` | *Robustness* | **PASSED** |
| 29 | `test_callbacks_and_queues` | `test_target_history_ring_buffer_limit` | Stabilitas Memori | **PASSED** |
| 30 | `test_callbacks_and_queues` | `test_update_ui_from_queues_sweep_and_target` | *IPC Queue* | **PASSED** |
| 31 | `test_callbacks_and_queues` | `test_cleanup_and_exit_sets_stop_event` | *Graceful Shutdown* | **PASSED** |
| 32 | `test_integration_pipeline` | `test_end_to_end_radar_detection_pipeline` | Integrasi *End-to-End* | **PASSED** |

---

## 4. Evaluasi Kualitas Perangkat Lunak (Quality Control Criteria)

### A. Akurasi Algoritma Pemrosesan Sinyal (DSP Precision)
* **Resolusi Frekuensi**: Pada frekuensi sampling 20 MS/s dengan ukuran buffer 20.000 sampel, resolusi bin frekuensi tercapai secara presisi sebesar **1,0 kHz per bin** ($\Delta f = rac{f_s}{N} = rac{20 	ext{ MHz}}{20.000} = 1 	ext{ kHz}$).
* **Kalibrasi Daya RF**: Perhitungan daya fisik sinyal pantulan diverifikasi tepat mengacu pada beban standar RF 50 $\Omega$ dengan formula:
  $$P_{	ext{mW}} = rac{V_{	ext{peak}}^2}{2 	imes 50} 	imes 1000 = 10 	imes V_{	ext{peak}}^2 \implies P_{	ext{dBm}} = 10 \log_{10}(P_{	ext{mW}})$$
  Hasil uji sinyal $0,5 	ext{ V}_{	ext{peak}}$ menghasilkan daya terkalibrasi $+3,98 	ext{ dBm}$ (sesuai nilai teoritis).
* **Peredaman Derau (Noise Grass Reduction)**: Filter *Savitzky-Golay* orde 3 berhasil meredam fluktuasi derau acak tanpa menggeser posisi frekuensi puncak target ($\Delta f_{	ext{error}} \le 2 	ext{ kHz}$).

### B. Keandalan dan Stabilitas Memori (Memory & Concurrency Safety)
* **Zero Memory Leak**: Struktur data riwayat target diverifikasi menggunakan `collections.deque(maxlen=50)`. Pengujian beban penambahan data berulang membuktikan alokasi memori bersifat konstan (*fixed upper bound*) dengan operasi penambahan $O(1)$, menghapuskan potensi akumulasi memori tak terbatas.
* **Thread Safety**: Komunikasi antar-*thread* diisolasi menggunakan modul bawaan Python `queue.Queue` yang menerapkan penguncian muteks internal (*reentrant mutex*), mencegah terjadinya *data race* atau tabrakan data antara *thread* akuisisi, pemrosesan data, dan *thread* antarmuka GUI.

---

## 5. Panduan Menjalankan Pengujian (Testing Execution SOP)

Untuk mereplikasi dan menjalankan seluruh rangkaian pengujian secara mandiri:

1. Aktifkan lingkungan virtual Python proyek:
   ```bash
   .\.venv\Scripts\activate
   ```
2. Jalankan seluruh pengujian unit dan integrasi:
   ```bash
   pytest
   ```
3. Menjalankan pengujian dengan laporan metrik cakupan kode (*coverage report*):
   ```bash
   pytest --cov=functions --cov=app --cov=config --cov-report=term-missing
   ```

---

## 6. Kesimpulan dan Pengesahan QA/QC

Berdasarkan seluruh hasil pengujian fungsional, pengujian numerik, pengujian integrasi, dan pengujian batas sistem yang telah dilaksanakan, perangkat lunak **Radar FMCW Real-Time & Spectrum Analyzer** dinyatakan:

**MEMENUHI SELURUH STANDAR MUTU TEKNIS DAN DINYATAKAN LOLOS PENGUJIAN QA/QC (QUALITY ASSURED).**

Bandung, 28 September 2026

**Tim Pengembang Perangkat Lunak / QA Engineer**  
Radar FMCW LPDP RISPRO  
