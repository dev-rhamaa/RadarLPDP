#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <conio.h>
#include <process.h>
#include <time.h>
#include "wddaskex.h"
#include "wd-dask.h"

// ----------------------- KONFIGURASI ------------------------------
// Jumlah kanal HW yang di-scan oleh 9846H (harus kontigu dari CH0)
#define TOTAL_HW_CHANNELS   4        // CH0..CH3
// Kanal yang ingin DISIMPAN (INDEX berbasiskan CH#)
static const int SELECTED_IDX[] = {1, 3}; // == CH1 & CH3
#define SELECTED_COUNT      (sizeof(SELECTED_IDX)/sizeof(SELECTED_IDX[0]))

#define SAMPLE_RATE_HZ      20000000
#define BUFFER_SAMPLES      8192
#define MAX_EVENT_BATCH     1000

#define LOG_FOLDER "log"
#define LIVE_FOLDER "live"
#define LIVE_UI_FILENAME "live_acquisition_ui.bin"

#define CODE_VERSION "Code trigger V.3"
#define AUTHOR_NAME  "Raihan Muhammad"

// -------------------- VARIABEL GLOBAL -----------------------------
static U16 card_type = PCI_9846H;
static U16 cardnum   = 0;
I16 card = -1;

// Buffer DMA untuk 4 kanal HW (interleaved CH0..CH3)
static U16 ai_buf [BUFFER_SAMPLES * TOTAL_HW_CHANNELS];
static U16 ai_buf2[BUFFER_SAMPLES * TOTAL_HW_CHANNELS];

U32 startPos, count1;

typedef struct {
    void* data;
    size_t size;
} AcquisitionData;

static AcquisitionData g_data_buffer[MAX_EVENT_BATCH];
static int g_buffered_count = 0;

// ----------------- FUNGSI SAVE BATCH ------------------------------
void save_batch_to_file() {
    if (g_buffered_count == 0) return;

    // 1. Buat nama file log batch yang unik
    time_t now = time(NULL);
    struct tm* t = localtime(&now);
    char log_filepath[MAX_PATH];
    snprintf(log_filepath, sizeof(log_filepath), "%s\\batch_log_%04d%02d%02d_%02d%02d%02d_%04d_evt.bin",
             LOG_FOLDER,
             t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
             t->tm_hour, t->tm_min, t->tm_sec, g_buffered_count);

    FILE* f_log = fopen(log_filepath, "wb");
    if (!f_log) {
        printf("KRITIS: Gagal membuat file batch log: %s\n", log_filepath);
        return;
    }

    // 2. Tulis header (pakai format string)
    char header[512];
    snprintf(header, sizeof(header),
        "TEST_DATE:%04d-%02d-%02d %02d:%02d:%02d\n"
        "CODE_VERSION:%s\n"
        "AUTHOR:%s\n"
        "BATCH_EVENT_COUNT:%d\n"
        "SAVED_CHANNELS:CH1,CH3\n"
        "INTERLEAVE_ORDER:CH1,CH3\n\n",
        t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
        t->tm_hour, t->tm_min, t->tm_sec,
        CODE_VERSION, AUTHOR_NAME, g_buffered_count
    );
    fwrite(header, 1, strlen(header), f_log);

    // 3. Tulis data event
    for (int i = 0; i < g_buffered_count; ++i) {
        fwrite(g_data_buffer[i].data, 1, g_data_buffer[i].size, f_log);
        free(g_data_buffer[i].data);
        g_data_buffer[i].data = NULL;
        g_data_buffer[i].size = 0;
    }
    fclose(f_log);
    printf("Batch %d event disimpan ke %s (header+data)\n", g_buffered_count, log_filepath);

    g_buffered_count = 0; // Reset buffer counter
}

// ------------------- UTILITY FUNGSI -------------------------------
void create_directory_if_not_exists(const char* path) {
    if (!CreateDirectory(path, NULL)) {
        if (GetLastError() != ERROR_ALREADY_EXISTS) {
            printf("Peringatan: Gagal membuat direktori '%s'. Error: %lu\n", path, GetLastError());
        }
    }
}

void print_error_and_cleanup(const char* message, I16 error_code) {
    printf("ERROR: %s, kode error: %d\n", message, error_code);
    if (card >= 0) {
        WD_AI_AsyncClear(card, NULL, NULL);
        WD_Release_Card(card);
        printf("Kartu DAQ dilepaskan.\n");
    }
    printf("Program berhenti karena error. Tekan tombol apa saja untuk keluar...\n");
    _getch();
    exit(1);
}

// Copy hanya kanal terpilih (CH1 & CH3) dari satu half-buffer DMA
// src  : pointer ke data interleaved CH0..CH3 (U16) sepanjang BUFFER_SAMPLES * TOTAL_HW_CHANNELS
// dst  : pointer buffer tujuan (cukup untuk BUFFER_SAMPLES * SELECTED_COUNT)
// Catatan: urutan output interleaved sesuai SELECTED_IDX (CH1,CH3)
static void extract_selected_channels(const U16* src, U16* dst) {
    const size_t N = BUFFER_SAMPLES;
    size_t out = 0;
    for (size_t i = 0; i < N; ++i) {
        size_t base = i * TOTAL_HW_CHANNELS;
        // tulis CH1 kemudian CH3
        for (int k = 0; k < SELECTED_COUNT; ++k) {
            int ch = SELECTED_IDX[k];
            dst[out++] = src[base + ch];
        }
    }
}

// -------------------- MAIN PROGRAM --------------------------------
int main() {
    I16 err, Id;
    U16 range;
    U32 samp_intrv;

    printf("Program Akuisisi Batch untuk PCI-9846H (SIMPAN HANYA CH1 & CH3)\n");
    printf("Live di folder '%s', log batch 1000 event di folder '%s'.\n", LIVE_FOLDER, LOG_FOLDER);
    printf("Tekan ESC untuk keluar.\n\n");

    create_directory_if_not_exists(LOG_FOLDER);
    create_directory_if_not_exists(LIVE_FOLDER);

    card = WD_Register_Card(card_type, cardnum);
    if (card < 0) { printf("Kesalahan WD_Register_Card: %d\n", card); return 1; }

    DAS_IOT_DEV_PROP cardProp;
    err = WD_GetDeviceProperties(card, 0, &cardProp);
    if (err != 0) print_error_and_cleanup("WD_GetDeviceProperties", err);

    range = cardProp.default_range;
    err = WD_AI_CH_Config(card, -1, range);
    if (err) print_error_and_cleanup("WD_AI_CH_Config", err);

    // Internal timebase, pacer timer
    err = WD_AI_Config(card, WD_IntTimeBase, 1, WD_AI_ADCONVSRC_TimePacer, 0, 1);
    if (err) print_error_and_cleanup("WD_AI_Config", err);

    samp_intrv = (U32)(40000000.0 / SAMPLE_RATE_HZ);
    if (samp_intrv < 2) samp_intrv = 2;
    printf("Sample Rate: %d Hz, Samp Intrv: %d\n", SAMPLE_RATE_HZ, samp_intrv);

    int event_count = 0;
    int exit_now = 0;

    while (!exit_now) {
        event_count++;

        // Trigger eksternal, post-trigger
        err = WD_AI_Trig_Config(card, WD_AI_TRGMOD_POST, WD_AI_TRGSRC_ExtD, WD_AI_TrgNegative,
                                0, 0.0, 0, 0, 0, 1);
        if (err) print_error_and_cleanup("WD_AI_Trig_Config", err);

        WD_AI_ContBufferReset(card);

        err = WD_AI_AsyncDblBufferMode(card, TRUE);
        if (err) print_error_and_cleanup("WD_AI_AsyncDblBufferMode", err);

        err = WD_AI_ContBufferSetup(card, ai_buf,  BUFFER_SAMPLES * TOTAL_HW_CHANNELS, &Id);
        if (err) print_error_and_cleanup("WD_AI_ContBufferSetup (buf1)", err);

        err = WD_AI_ContBufferSetup(card, ai_buf2, BUFFER_SAMPLES * TOTAL_HW_CHANNELS, &Id);
        if (err) print_error_and_cleanup("WD_AI_ContBufferSetup (buf2)", err);

        // Scan CH0..CH3 (TOTAL_HW_CHANNELS-1 = 3)
        err = WD_AI_ContScanChannels(card, TOTAL_HW_CHANNELS - 1, Id,
                                     BUFFER_SAMPLES, samp_intrv, samp_intrv, ASYNCH_OP);
        if (err) print_error_and_cleanup("WD_AI_ContScanChannels", err);

        // Tunggu trigger armed
        U32 trig_status = 0;
        do {
            WD_AI_ContStatus(card, &trig_status);
            if (_kbhit() && _getch() == 27) { exit_now = 1; break; }
        } while (!(trig_status & 0x4) && !exit_now);

        if (exit_now) break;

        // ------------------- TULIS FILE LIVE (TEMP > FINAL) ------------------------
        char live_filepath_tmp[MAX_PATH], live_filepath_final[MAX_PATH];
        snprintf(live_filepath_tmp, sizeof(live_filepath_tmp), "%s\\live_acquisition_ui.tmp", LIVE_FOLDER);
        snprintf(live_filepath_final, sizeof(live_filepath_final), "%s\\%s", LIVE_FOLDER, LIVE_UI_FILENAME);
        FILE* f_out_live = fopen(live_filepath_tmp, "wb");
        if (!f_out_live) {
            // Jika gagal bikin file live, tetap lanjut akuisisi dan batching
            // agar tidak kehilangan data event.
        }
        // ----------------------------------------------------------------------------

        void* current_acq_buffer = NULL;
        size_t current_acq_size = 0;

        const size_t hw_chunk_samps  = BUFFER_SAMPLES * TOTAL_HW_CHANNELS;         // sampel U16 per half
        const size_t sel_chunk_samps = BUFFER_SAMPLES * SELECTED_COUNT;            // untuk CH1 & CH3
        const size_t sel_chunk_bytes = sel_chunk_samps * sizeof(U16);

        int g_fStop = 0;
        BOOLEAN halfReady;
        int current_buffer_idx = 0;

        // Buffer kerja untuk hasil ekstraksi CH1 & CH3 dari setiap half
        U16* sel_work = (U16*)malloc(sel_chunk_bytes);
        if (!sel_work) {
            print_error_and_cleanup("Alokasi sel_work", -1);
        }

        while (!g_fStop) {
            WD_AI_AsyncDblBufferHalfReady(card, &halfReady, (BOOLEAN*)&g_fStop);
            if (halfReady) {
                // Sumber: half buffer dari DMA (HW interleaved CH0..CH3)
                const U16* source_buffer = (const U16*)((current_buffer_idx == 0) ? ai_buf : ai_buf2);

                // Ekstrak CH1 & CH3 ke buffer kerja
                extract_selected_channels(source_buffer, sel_work);

                // Tambah ke buffer RAM event (hanya CH1 & CH3)
                void* new_buffer = realloc(current_acq_buffer, current_acq_size + sel_chunk_bytes);
                if (new_buffer == NULL) {
                    // Jika gagal alokasi, hentikan akuisisi event ini (tanpa crash)
                    free(current_acq_buffer);
                    current_acq_buffer = NULL;
                    current_acq_size = 0;
                    g_fStop = 1;
                } else {
                    current_acq_buffer = new_buffer;
                    memcpy((char*)current_acq_buffer + current_acq_size, sel_work, sel_chunk_bytes);
                    current_acq_size += sel_chunk_bytes;

                    // Tulis ke file live (kalau berhasil dibuka)
                    if (f_out_live) {
                        fwrite(sel_work, 1, sel_chunk_bytes, f_out_live);
                    }
                }

                // Beri tahu driver bahwa half-buffer sudah diproses
                current_buffer_idx = 1 - current_buffer_idx;
                WD_AI_AsyncDblBufferHandled(card);
            }

            if (_kbhit() && _getch() == 27) { g_fStop = 1; exit_now = 1; }
        }

        // Selesai akuisisi untuk event ini
        if (f_out_live) {
            fclose(f_out_live);
            MoveFileExA(live_filepath_tmp, live_filepath_final,
                        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
        }

        // PENTING: Clear sekali di sini (bukan di dalam loop halfReady)
        WD_AI_AsyncClear(card, &startPos, &count1);

        free(sel_work);

        if (current_acq_buffer != NULL && current_acq_size > 0) {
            // Simpan data event ke buffer RAM untuk batch
            g_data_buffer[g_buffered_count].data = current_acq_buffer;
            g_data_buffer[g_buffered_count].size = current_acq_size;
            g_buffered_count++;

            // Jika buffer sudah 1000 event, simpan batch ke file log
            if (g_buffered_count >= MAX_EVENT_BATCH) {
                save_batch_to_file();
            }
        } else {
            // Tidak ada data (misal gagal alokasi); lanjut ke event berikutnya
        }
    }

    // Simpan sisa batch sebelum keluar
    if (g_buffered_count > 0) {
        save_batch_to_file();
    }

    if (card >= 0) {
        // Sudah di-AsyncClear per event; ini hanya jaga-jaga
        WD_AI_AsyncClear(card, NULL, NULL);
        WD_Release_Card(card);
        printf("Kartu DAQ dilepaskan.\n");
    }

    printf("\nProgram selesai. Tekan tombol apa saja untuk keluar...\n");
    _getch();
    return 0;
}
