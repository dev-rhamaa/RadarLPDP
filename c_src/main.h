#ifndef MAIN_H
#define MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <windows.h>

#ifdef BUILDING_DAQ_DLL
    #define DAQ_API __declspec(dllexport)
#else
    #define DAQ_API __declspec(dllimport)
#endif

/* Hardware defaults matching PCI-9846H & cadgetdatanew.c */
#define DEFAULT_CARD_TYPE       0x17    /* PCI_9846H */
#define DEFAULT_CARD_NUM        0
#define DEFAULT_SAMPLE_RATE_HZ  20000000 /* 20 MS/s */
#define DEFAULT_BUFFER_SAMPLES  20000   /* 20,000 samples per channel (1 ms) */
#define DAQ_CHANNEL_COUNT       2       /* CH0, CH2 */

/**
 * Inisialisasi kartu DAQ ADLink PCI-9846H.
 * Mengonfigurasi range input, timebase, external digital trigger (negative edge, post-trigger),
 * dan continuous restart DMA double buffer.
 *
 * @param card_num Index kartu (default 0)
 * @param sample_rate Sampling rate dalam Hz (default 20,000,000)
 * @param buffer_samples Jumlah sample per kanal per buffer (default 20,000)
 * @return 0 jika sukses, atau kode error negatif
 */
DAQ_API int daq_init(uint16_t card_num, uint32_t sample_rate, uint32_t buffer_samples);

/**
 * Memulai continuous multi-channel asynchronous DMA acquisition pada CH0 & CH2.
 *
 * @return 0 jika sukses, kode error ADLink jika gagal
 */
DAQ_API int daq_start(void);

/**
 * Cek apakah event baru telah tertrigger dan buffer DMA siap dibaca.
 * Non-blocking check menggunakan WD_AI_AsyncReStartNextReady.
 *
 * @param is_ready Output: 1 jika data siap, 0 jika belum ada trigger
 * @param ready_buffer_idx Output: index buffer aktif (0 atau 1)
 * @return 0 jika normal, kode error jika terjadi kegagalan hardware
 */
DAQ_API int daq_poll_event(int* is_ready, uint16_t* ready_buffer_idx);

/**
 * Salin data kanal CH0 dan CH2 yang telah di-deinterleave langsung ke buffer Python.
 * Fungsi ini memproses buffer DMA yang siap dan menyalinnya ke memori tujuan.
 *
 * @param ch0_dest Pointer ke array output uint16 untuk CH0
 * @param ch2_dest Pointer ke array output uint16 untuk CH2
 * @param max_samples Kapasitas maksimal elemen array tujuan
 * @return Jumlah sample per channel yang berhasil disalin, atau negatif jika error
 */
DAQ_API int daq_read_channels(uint16_t* ch0_dest, uint16_t* ch2_dest, uint32_t max_samples);

/**
 * Mendapatkan pointer memori internal de-interleaved CH0 dan CH2 secara Zero-Copy.
 * Sangat efisien untuk dipetakan langsung oleh NumPy / ctypes tanpa alokasi memori tambahan.
 *
 * @param ch0_ptr Output: pointer ke data internal CH0
 * @param ch2_ptr Output: pointer ke data internal CH2
 * @param sample_count Output: jumlah sample per channel yang valid
 * @return 1 jika data baru tersedia, 0 jika belum ada data baru
 */
DAQ_API int daq_get_channel_pointers(const uint16_t** ch0_ptr, const uint16_t** ch2_ptr, uint32_t* sample_count);

/**
 * Menghentikan proses akuisisi continuous DMA dan membersihkan status buffer.
 *
 * @return 0 jika sukses
 */
DAQ_API int daq_stop(void);

/**
 * Melepaskan kartu DAQ hardware dari sistem.
 */
DAQ_API void daq_release(void);

/**
 * Mendapatkan total jumlah event/trigger yang telah berhasil diakuisisi sejak start.
 *
 * @return Total event count
 */
DAQ_API uint32_t daq_get_event_count(void);

/**
 * Cek apakah engine akuisisi sedang aktif berjalan.
 *
 * @return 1 jika aktif, 0 jika berhenti
 */
DAQ_API int daq_is_active(void);

#ifdef __cplusplus
}
#endif

#endif /* MAIN_H */
