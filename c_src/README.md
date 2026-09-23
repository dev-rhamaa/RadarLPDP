# 📡 DAQ Hardware C Integration (`c_src/`)

Direktori ini menyediakan pustaka driver C dan berkas header resmi untuk kartu akuisisi data **ADLink PCI-9846H**. Modul ini digunakan oleh antarmuka akuisisi Python [app/c_acquisition.py](file:///c:/RadarLPDP/app/c_acquisition.py) untuk mengalirkan data sampling multi-kanal (CH0 & CH2) langsung ke memori RAM (*Zero-Copy streaming*) tanpa memerlukan penulisan buffer ke file biner (`.bin`).

---

## 📁 Struktur Direktori

```
c_src/
├── include/
│   ├── Wd-dask64.h     # Berkas header resmi ADLink WD-Dask 64-bit API
│   └── wddaskex.h      # Deklarasi properti kartu dan konfigurasi IoT DAQ
├── lib/
│   └── wd-dask64.dll   # Pustaka biner driver ADLink WD-Dask 64-bit (Active Driver)
└── README.md           # Dokumentasi modul ini
```

---

## 🔌 Mekanisme Integrasi Python (`ctypes`)

Aplikasi radar memanggil driver C [wd-dask64.dll](file:///c:/RadarLPDP/c_src/lib/wd-dask64.dll) secara langsung menggunakan pustaka bawaan Python `ctypes`:

1. **Memuat Driver Dinamis**: `ctypes.WinDLL("c_src/lib/wd-dask64.dll")`
2. **Konfigurasi Kartu PCI-9846H**:
   - `WD_Register_Card(PCI_9846H, card_num)`
   - `WD_AI_CH_Config(card, ch, AD_B_1_V)`
   - `WD_AI_Config(card, WD_IntTimeBase, ...)`
   - `WD_AI_Trig_Config(card, WD_AI_TRGMOD_POST, WD_AI_TRGSRC_ExtD, WD_AI_TrgNegative, ...)`
3. **Double Buffer DMA & Continuous Restart**:
   - `WD_AI_AsyncDblBufferMode(card, True)`
   - `WD_AI_ContReadMultiChannels(..., ASYNCH_OP)`
   - Polling event melalui `WD_AI_AsyncReStartNextReady(...)`
4. **Zero-Copy Memory Mapping ke NumPy**:
   - `np.ctypeslib.as_array(buffer)` langsung memetakan pointer memori fisik DMA ke array NumPy tanpa *copy overhead*.
