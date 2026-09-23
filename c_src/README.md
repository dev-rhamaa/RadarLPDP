# 📡 DAQ C Core Module (`c_src/`)

Direktori ini berisi kode sumber C dan pustaka pendukung untuk antarmuka kartu akuisisi ADLink PCI-9846H. Modul ini dirancang khusus untuk menyediakan data sampling secara langsung (*in-memory*) ke aplikasi Python [main.py](file:///c:/RadarLPDP/main.py) tanpa memerlukan penulisan buffer ke file biner (`.bin`).

---

## 📁 Struktur Direktori

```
c_src/
├── main.c           # Implementasi C modul akuisisi DAQ
├── main.h           # Header deklarasi fungsi ekspor API C
├── include/         # Header SDK ADLink (wd-dask.h, Wd-dask64.h, wddaskex.h)
├── lib/             # Pustaka binary DLL driver ADLink (wd-dask64.dll, WD-Dask.dll)
└── README.md        # Dokumentasi modul ini
```

---

## 🔌 API Antarmuka C untuk Python

| Fungsi | Deskripsi |
| :--- | :--- |
| `daq_init(card_num, sample_rate, buffer_samples)` | Mendaftarkan kartu PCI-9846H, mengonfigurasi range input, trigger digital eksternal (negative edge), restart continuous DMA mode, dan double buffer. |
| `daq_start()` | Memulai akuisisi data continuous multi-kanal pada CH0 dan CH2. |
| `daq_poll_event(is_ready, ready_buffer_idx)` | Memeriksa ketersediaan event pemicu (*trigger*) baru secara asinkron (non-blocking). |
| `daq_read_channels(ch0_dest, ch2_dest, max_samples)` | Mengambil buffer DMA aktif, men-deinterleave CH0 dan CH2, dan menyalinnya langsung ke array buffer tujuan. |
| `daq_get_channel_pointers(ch0_ptr, ch2_ptr, sample_count)` | Memberikan pointer langsung ke array data internal untuk akses **Zero-Copy** dari NumPy. |
| `daq_stop()` | Menghentikan operasi continuous DMA dan me-reset buffer kartu. |
| `daq_release()` | Melepaskan kartu DAQ hardware dan membebaskan alokasi memori RAM. |
| `daq_get_event_count()` | Mengembalikan jumlah total event yang telah berhasil diakuisisi. |
| `daq_is_active()` | Memeriksa apakah status akuisisi sedang aktif. |

---

## ⚙️ Kompilasi ke Shared Library (DLL)

Jika ingin mengompilasi menjadi DLL menggunakan GCC:
```powershell
gcc -shared -O3 -DBUILDING_DAQ_DLL -I c_src/include c_src/main.c -L c_src/lib -lwd-dask64 -o c_src/lib/daq_engine.dll
```

Aplikasi Python [app/c_acquisition.py](file:///c:/RadarLPDP/app/c_acquisition.py) memuat driver `wd-dask64.dll` secara langsung melalui `ctypes` dengan arsitektur pipeline yang identik dengan implementasi pada [main.c](file:///c:/RadarLPDP/c_src/main.c).
