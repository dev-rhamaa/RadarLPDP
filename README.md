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

## Catatan Kalibrasi Motor Servo (Datasheet)

Acuan utama: datasheet driver `KYDAS4X01A DC servo motor driver.pdf`, motor `KY80ACS0407-30` dan gearbox `AB.pdf` (090-L2, rasio **80:1**).

| Besaran | Nilai | Sumber |
|---|---|---|
| Encoder motor | 2500 ppr (incremental magnetic) | datasheet motor |
| Skala posisi driver | 10.000 counts / putaran motor (2500 x 4 quadrature) | datasheet driver (`10000/circle`) |
| Rasio gearbox | 80:1 | gearbox terpasang |
| Backlash gearbox | P1 <= 4 arcmin, P2 <= 6 arcmin (0,067 - 0,1 deg) | datasheet gearbox |

Perhitungan:

```
counts per putaran antena = 10.000 x 80      = 800.000
counts per 1 derajat      = 800.000 / 360    = 2.222,22
1 count                   = 0,00045 deg
```

-   **1 derajat antena = 2.222,22 counts**
-   **1 putaran 360 deg = 800.000 counts**
-   Arah: counts **positif = kiri**, counts **negatif = kanan** (counts makin negatif, sudut makin besar).

### Beda dengan kalibrasi lama di `config.py`

Kalibrasi lama (hasil percobaan) memakai 130.000 counts per 60 deg = 2.166,67 counts/deg, setara rasio efektif sekitar 78:1, selisih 2,5% dari datasheet. Akibatnya, perintah 60 deg dari tengah (130.000 counts) secara teori hanya menggerakkan antena sekitar 58,5 deg. Dengan angka datasheet, +-60 deg = +-133.333 counts.

Skala yang dipakai aplikasi saat ini masih hasil percobaan: `SERVO_COUNTS_PER_DEG = 130_000 / 60` di `config.py` (perilaku sama seperti sebelumnya). Nilai datasheet (2.222,22) belum dipakai; verifikasi dulu dengan pengukuran langsung (baca `ED 08` sebelum dan sesudah memutar antena sejauh sudut yang diketahui), lalu ganti satu konstanta itu.

### Titik tengah tidak lagi di-hardcode

`SERVO_CENTER_POSITION`, `SERVO_TARGET_30_DEG`, dan `SERVO_TARGET_150_DEG` sudah dihapus dari `config.py`. Alurnya sekarang:

1.  Saat `main.py` pertama kali terhubung ke driver, posisi motor saat itu (`ED 08`) dibaca dan dijadikan **titik tengah = 90 deg**. Nilai counter absolut tidak penting (counter encoder incremental selalu mulai dari 0 saat driver dinyalakan).
2.  Semua target dihitung relatif terhadap titik itu: `counts = tengah + (90 - derajat) x SERVO_COUNTS_PER_DEG` (counts positif = kiri, negatif = kanan). Sapuan tetap 30 sampai 150 deg, bolak-balik.
3.  Saat motor di-STOP atau aplikasi ditutup, motor kembali ke titik tengah itu, sehingga motor selalu parkir di 90 deg.
4.  Titik tengah tidak diambil ulang kalau koneksi serial terputus lalu tersambung lagi dalam satu sesi, supaya tidak bergeser ke tengah sapuan.
5.  `servo_state.json` tidak lagi menyimpan counts, hanya `running`, `mode`, dan `target_deg`.

**Syarat**: antena harus berada di 90 deg ketika aplikasi dibuka (dan driver dinyalakan). Kalau tidak, seluruh sektor ikut bergeser. Gunakan `centering_tool.py` untuk mengatur posisi antena sebelum menjalankan `main.py`.

## Tool Centering Motor (`centering_tool.py`)

Mini app untuk menggeser motor ke kiri/kanan sampai antena tepat di tengah (90 deg).

```bash
python centering_tool.py
```

-   Tutup `main.py` dulu: port serial (default `COM13`, lihat `config.py`) tidak bisa dipakai dua program sekaligus.
-   Isi port, klik **Hubungkan**. Posisi saat itu dijadikan acuan jendela gerak.
-   **<< KIRI** / **KANAN >>** menggeser motor sebesar langkah terpilih (0,1 / 0,5 / 1 / 5 deg per klik, dikonversi dengan 2.222,22 counts/deg).
-   **Batas gerak: 1 putaran = 800.000 counts** (+-400.000 dari titik tengah). Klik di luar batas ditolak dan ditampilkan pesan.
-   **Tandai TENGAH (90 deg)** memindahkan jendela batas 800.000 counts di tool ini ke posisi riil sekarang dan mencetak nilainya di terminal. Tidak ada angka yang perlu disalin ke `config.py`: setelah antena pas di 90 deg, tutup tool ini dan jalankan `main.py`, yang otomatis memakai posisi motor saat itu sebagai titik tengah.
-   **DISABLE motor** melepas motor (perintah `E0 00 ...`). Klik KIRI/KANAN untuk mengaktifkan lagi.
-   Tool ini tidak mengubah `config.py` atau `servo_state.json` secara otomatis.
