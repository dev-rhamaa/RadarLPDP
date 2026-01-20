# Real-time Radar UI & Spectrum Analyzer

Sebuah dasbor antarmuka pengguna (UI) yang komprehensif untuk visualisasi data secara real-time, dibangun dengan Python dan Dear PyGui. Proyek ini mendemonstrasikan praktik terbaik untuk membangun aplikasi yang responsif menggunakan arsitektur multithreading untuk menangani pemrosesan data yang berat tanpa membuat UI membeku (freeze).



## Fitur Utama

-   **Dasbor Multi-Widget**: Layout yang terorganisir dengan beberapa panel yang berjalan secara bersamaan.
-   **Tampilan PPI (Plan Position Indicator) Real-time**:
    -   Digambar secara kustom dari awal menggunakan API gambar Dear PyGui.
    -   Sapuan jarum (sweep) 180 derajat yang bergerak bolak-balik.
    -   Efek *persistence* (jejak pudar) yang realistis pada sapuan jarum.
    -   Menampilkan target statis (blips).
    -   Desain visual yang menyatu dengan tema aplikasi lainnya.
-   **Spectrum Analyzer (FFT) Real-time**:
    -   Secara otomatis memantau file data biner (`.bin`) untuk perubahan.
    -   Saat file diperbarui, data dimuat, diproses (FFT), dan ditampilkan di plot.
-   **Waveform Display Real-time**:
    -   Juga memantau file data biner yang sama.
    -   Menampilkan data mentah dalam domain waktu (amplitudo vs. waktu).
-   **Arsitektur Multithreading yang Kuat**:
    -   UI berjalan di *main thread*, sementara setiap widget pemrosesan data (PPI, FFT, Sinewave) memiliki *worker thread* sendiri.
    -   Komunikasi aman antar thread menggunakan `queue.Queue` untuk mencegah *race conditions*.
    -   UI tetap **100% responsif** bahkan saat file besar sedang diproses di latar belakang.
-   **Layout Fullscreen & Responsif**: Aplikasi berjalan dalam mode fullscreen dan layoutnya secara otomatis menyesuaikan diri dengan ukuran layar.
-   **Kontrol Intuitif**: Tekan tombol `Esc` untuk keluar dari aplikasi dengan aman.

## Arsitektur

Proyek ini menggunakan pola desain UI yang umum untuk aplikasi data-intensif:

1.  **UI Thread (Main Thread)**: Thread ini hanya bertanggung jawab untuk menggambar antarmuka dan merespons input pengguna. Thread ini tidak pernah melakukan pekerjaan yang memakan waktu.
2.  **Worker Threads**: Setiap tugas berat (membaca file, kalkulasi FFT, menggerakkan PPI) dijalankan di thread terpisah. Hal ini memastikan UI tidak pernah "menunggu" tugas selesai.
3.  **Queue System**: Setiap *worker thread* memiliki `queue` sebagai "kotak surat". Setelah worker selesai memproses data, ia menempatkan hasilnya di dalam queue.
4.  **Render Loop**: *Main thread* memiliki *render loop* (`while dpg.is_dearpygui_running():`) yang pada setiap frame memeriksa semua queue. Jika ada data baru, data tersebut diambil dan digunakan untuk memperbarui plot di layar.

## Struktur Proyek

```
UI/
├── widgets/
│   ├── __init__.py           # Membuat 'widgets' menjadi Python package
│   ├── PPI.py                # Widget untuk tampilan radar (custom drawing)
│   ├── FFT.py                # Widget untuk analisis spektrum (memantau file)
│   ├── Sinewave.py           # Widget untuk tampilan waveform (memantau file)
│   ├── logo.py         # Placeholder untuk kontrol
│   └── file.py               # Placeholder untuk file explorer
├── main.py                   # Titik masuk utama aplikasi, mengatur layout dan thread
├── simulate_acquisition.py   # Skrip untuk mensimulasikan update file data .bin
└── README.md                 # Dokumentasi ini
```

## Teknologi yang Digunakan

-   **Python 3**
-   **Dear PyGui** (v2.x): Untuk semua elemen antarmuka dan gambar.
-   **NumPy**: Untuk operasi numerik yang efisien pada data.
-   **SciPy**: Khususnya untuk fungsi Fast Fourier Transform (`scipy.fft`).

## Penyiapan dan Instalasi

1.  **Prasyarat**: Pastikan Anda memiliki Python 3.8 atau yang lebih baru terinstal.

2.  **Clone atau Unduh Proyek**: Dapatkan semua file proyek ke komputer lokal Anda.

3.  **Buat Lingkungan Virtual (Sangat Direkomendasikan)**:
    Buka terminal di dalam folder `UI/` dan jalankan:
    ```bash
    # Membuat lingkungan virtual bernama '.venv'
    python -m venv .venv

    # Mengaktifkan lingkungan (Linux/macOS)
    source .venv/bin/activate

    # Atau mengaktifkan lingkungan (Windows)
    .\.venv\Scripts\activate
    ```

4.  **Instal Dependensi**:
    Buat file bernama `requirements.txt` di dalam folder `UI/` dengan isi berikut:
    ```txt
    dearpygui
    numpy
    scipy
    ```
    Kemudian, instal semua dependensi dengan satu perintah:
    ```bash
    pip install -r requirements.txt
    ```

## Cara Menjalankan

Karena widget FFT dan Sinewave dirancang untuk memantau file yang berubah, Anda perlu dua terminal untuk mengujinya.

1.  **Terminal 1: Jalankan Simulator Akuisisi Data**
    Di terminal pertama (dengan lingkungan virtual aktif), jalankan skrip simulator. Skrip ini akan membuat dan secara periodik memperbarui file `live_acquisition_ui.bin`.
    ```bash
    python simulate_acquisition.py
    ```
    Biarkan terminal ini berjalan di latar belakang.

2.  **Terminal 2: Jalankan Aplikasi Utama**
    Buka terminal *kedua* di folder yang sama (dan aktifkan lingkungan virtual jika perlu). Jalankan aplikasi utama.
    ```bash
    python main.py
    ```

3.  **Nikmati!**
    Aplikasi akan terbuka dalam mode fullscreen. Anda akan melihat:
    -   Tampilan PPI bergerak dengan lancar.
    -   Plot FFT dan Waveform secara otomatis diperbarui setiap kali skrip simulator menulis ke file.
    -   Tekan tombol `Esc` untuk keluar.