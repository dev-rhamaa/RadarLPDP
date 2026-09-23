#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <conio.h>
#include <time.h>

#include "wddaskex.h"
#include "wd-dask.h"


// ================================================================
// KONFIGURASI
// ================================================================

#define CHANNEL_COUNT       2

// 20 MS/s
#define SAMPLE_RATE_HZ      20000000

// 20.000 sample/channel
// Jika sampling 20 MS/s:
// 20.000 sample = 1 ms
#define BUFFER_SAMPLES      20000

// Simpan 1000 event sebelum dibuat batch log
#define MAX_EVENT_BATCH     1000


// Folder output
#define LOG_FOLDER          "log"
#define LIVE_FOLDER         "live"

// Nama file live yang dibaca UI
#define LIVE_UI_FILENAME    "live_acquisition_ui.bin"

// File temporary live
#define LIVE_TMP_FILENAME   "live_acquisition_ui.tmp"


// Informasi program
#define CODE_VERSION        "Code trigger V.4"
#define AUTHOR_NAME         "Raihan Muhammad"


// ================================================================
// GLOBAL
// ================================================================

static U16 card_type = PCI_9846H;
static U16 cardnum   = 0;

static I16 card = -1;


// ----------------------------------------------------------------
// Buffer hardware
//
// BUFFER_SAMPLES = jumlah sample PER CHANNEL
//
// Karena ada 2 channel:
// CH0, CH2
//
// jumlah U16 dalam satu buffer:
// 20.000 x 2 = 40.000 U16
//
// ukuran:
// 40.000 x 2 byte = 80.000 byte
// ----------------------------------------------------------------

static U16 ai_buf[BUFFER_SAMPLES * CHANNEL_COUNT];
static U16 ai_buf2[BUFFER_SAMPLES * CHANNEL_COUNT];


// ID buffer dari WD-DASK
static I16 Id1 = -1;
static I16 Id2 = -1;


// ----------------------------------------------------------------
// Buffer batch
// ----------------------------------------------------------------

typedef struct
{
    void*  data;
    size_t size;

} AcquisitionData;


static AcquisitionData g_data_buffer[MAX_EVENT_BATCH];

static int g_buffered_count = 0;


// ================================================================
// CLEANUP BATCH
// ================================================================

static void free_batch_buffer(void)
{
    int i;

    for (i = 0; i < MAX_EVENT_BATCH; i++)
    {
        if (g_data_buffer[i].data != NULL)
        {
            free(g_data_buffer[i].data);

            g_data_buffer[i].data = NULL;
            g_data_buffer[i].size = 0;
        }
    }

    g_buffered_count = 0;
}


// ================================================================
// SAVE BATCH
// ================================================================

static void save_batch_to_file(void)
{
    time_t now;
    struct tm* t;

    char log_filepath[MAX_PATH];

    FILE* f_log;

    char header[512];

    int i;

    int events_to_save;


    if (g_buffered_count <= 0)
        return;


    // ------------------------------------------------------------
    // Waktu
    // ------------------------------------------------------------

    now = time(NULL);
    t = localtime(&now);

    if (t == NULL)
    {
        printf("ERROR: Gagal mendapatkan waktu sistem.\n");
        return;
    }


    events_to_save = g_buffered_count;


    // ------------------------------------------------------------
    // Nama file batch
    // ------------------------------------------------------------

    snprintf(
        log_filepath,
        sizeof(log_filepath),

        "%s\\batch_log_%04d%02d%02d_%02d%02d%02d_%04d_evt.bin",

        LOG_FOLDER,

        t->tm_year + 1900,
        t->tm_mon + 1,
        t->tm_mday,

        t->tm_hour,
        t->tm_min,
        t->tm_sec,

        events_to_save
    );


    // ------------------------------------------------------------
    // Buka file
    // ------------------------------------------------------------

    f_log = fopen(log_filepath, "wb");

    if (f_log == NULL)
    {
        printf(
            "KRITIS: Gagal membuat file batch log: %s\n",
            log_filepath
        );

        return;
    }


    // ------------------------------------------------------------
    // Header
    // ------------------------------------------------------------

    snprintf(
        header,
        sizeof(header),

        "TEST_DATE:%04d-%02d-%02d %02d:%02d:%02d\n"
        "CODE_VERSION:%s\n"
        "AUTHOR:%s\n"
        "CARD:PCI-9846H\n"
        "CHANNEL_COUNT:%d\n"
        "CHANNELS:CH0,CH2\n"
        "SAMPLE_RATE:%d\n"
        "SAMPLES_PER_CHANNEL:%d\n"
        "EVENT_DATA_FORMAT:CH0,CH2_INTERLEAVED\n"
        "EVENT_SIZE_BYTES:%zu\n"
        "BATCH_EVENT_COUNT:%d\n"
        "\n",

        t->tm_year + 1900,
        t->tm_mon + 1,
        t->tm_mday,

        t->tm_hour,
        t->tm_min,
        t->tm_sec,

        CODE_VERSION,
        AUTHOR_NAME,

        CHANNEL_COUNT,

        SAMPLE_RATE_HZ,

        BUFFER_SAMPLES,

        sizeof(U16) *
        BUFFER_SAMPLES *
        CHANNEL_COUNT,

        events_to_save
    );


    fwrite(
        header,
        1,
        strlen(header),
        f_log
    );


    // ------------------------------------------------------------
    // Data event
    // ------------------------------------------------------------

    for (i = 0; i < events_to_save; i++)
    {
        if (g_data_buffer[i].data != NULL &&
            g_data_buffer[i].size > 0)
        {
            fwrite(
                g_data_buffer[i].data,
                1,
                g_data_buffer[i].size,
                f_log
            );
        }
    }


    fclose(f_log);


    // ------------------------------------------------------------
    // Free memory
    // ------------------------------------------------------------

    for (i = 0; i < events_to_save; i++)
    {
        if (g_data_buffer[i].data != NULL)
        {
            free(g_data_buffer[i].data);

            g_data_buffer[i].data = NULL;
            g_data_buffer[i].size = 0;
        }
    }


    g_buffered_count = 0;


    printf(
        "\nBatch %d event berhasil disimpan:\n%s\n\n",
        events_to_save,
        log_filepath
    );
}


// ================================================================
// CREATE DIRECTORY
// ================================================================

static void create_directory_if_not_exists(
    const char* path
)
{
    if (!CreateDirectoryA(path, NULL))
    {
        DWORD err = GetLastError();

        if (err != ERROR_ALREADY_EXISTS)
        {
            printf(
                "Peringatan: gagal membuat direktori '%s'. "
                "Error: %lu\n",
                path,
                err
            );
        }
    }
}


// ================================================================
// CLEANUP CARD
// ================================================================

static void cleanup_card(void)
{
    if (card >= 0)
    {
        WD_AI_AsyncClear(
            card,
            NULL,
            NULL
        );

        WD_AI_ContBufferReset(card);

        WD_Release_Card(card);

        card = -1;

        printf(
            "\nKartu DAQ dilepaskan.\n"
        );
    }
}


// ================================================================
// ERROR HANDLER
// ================================================================

static void print_error_and_cleanup(
    const char* message,
    I16 error_code
)
{
    printf(
        "\n==================================================\n"
        "ERROR\n"
        "==================================================\n"
        "%s\n"
        "Kode error : %d\n"
        "==================================================\n",
        message,
        error_code
    );

    cleanup_card();

    free_batch_buffer();

    printf(
        "\nProgram berhenti karena error.\n"
    );

    printf(
        "Tekan tombol apa saja untuk keluar..."
    );

    _getch();

    exit(1);
}


// ================================================================
// SAVE LIVE EVENT
//
// File ditulis ke .tmp terlebih dahulu.
//
// Setelah selesai:
// .tmp -> live_acquisition_ui.bin
//
// Jadi UI tidak membaca file setengah jadi.
// ================================================================

static int save_live_event(
    const void* data,
    size_t data_size
)
{
    char tmp_path[MAX_PATH];
    char final_path[MAX_PATH];

    FILE* f;


    snprintf(
        tmp_path,
        sizeof(tmp_path),
        "%s\\%s",
        LIVE_FOLDER,
        LIVE_TMP_FILENAME
    );


    snprintf(
        final_path,
        sizeof(final_path),
        "%s\\%s",
        LIVE_FOLDER,
        LIVE_UI_FILENAME
    );


    // Hapus temporary lama jika ada
    DeleteFileA(tmp_path);


    // ------------------------------------------------------------
    // Buat temporary file
    // ------------------------------------------------------------

    f = fopen(tmp_path, "wb");

    if (f == NULL)
    {
        printf(
            "WARNING: Tidak dapat membuka live temporary file.\n"
        );

        return 0;
    }


    // ------------------------------------------------------------
    // Tulis event
    // ------------------------------------------------------------

    if (fwrite(
            data,
            1,
            data_size,
            f
        ) != data_size)
    {
        fclose(f);

        DeleteFileA(tmp_path);

        printf(
            "WARNING: Gagal menulis live file.\n"
        );

        return 0;
    }


    fflush(f);

    fclose(f);


    // ------------------------------------------------------------
    // Rename temporary -> final
    // ------------------------------------------------------------

    if (!MoveFileExA(
            tmp_path,
            final_path,
            MOVEFILE_REPLACE_EXISTING |
            MOVEFILE_WRITE_THROUGH
        ))
    {
        printf(
            "WARNING: Gagal mengganti live file. "
            "Windows error: %lu\n",
            GetLastError()
        );

        DeleteFileA(tmp_path);

        return 0;
    }


    return 1;
}


// ================================================================
// MAIN
// ================================================================

int main(void)
{
    I16 err;

    U16 range;

    U32 samp_intrv;

    U32 samples_per_buffer;

    size_t event_size_bytes;

    U16 ch_list[CHANNEL_COUNT] =
    {
        0,
        2
    };


    int exit_now = 0;

    unsigned long event_count = 0;


    // ============================================================
    // INFORMASI PROGRAM
    // ============================================================

    printf(
        "\n"
        "============================================================\n"
        "        PCI-9846H RADAR DATA ACQUISITION\n"
        "============================================================\n"
        "Code Version : %s\n"
        "Author       : %s\n"
        "Channels     : CH0, CH2\n"
        "Sample Rate  : %d Hz\n"
        "Samples/Ch   : %d\n"
        "Event Time   : %.3f ms\n"
        "Live File    : %s\\%s\n"
        "Batch Size   : %d events\n"
        "============================================================\n"
        "\n",

        CODE_VERSION,
        AUTHOR_NAME,

        SAMPLE_RATE_HZ,

        BUFFER_SAMPLES,

        ((double)BUFFER_SAMPLES /
         (double)SAMPLE_RATE_HZ) *
        1000.0,

        LIVE_FOLDER,
        LIVE_UI_FILENAME,

        MAX_EVENT_BATCH
    );


    printf(
        "Tekan ESC kapan saja untuk menghentikan akuisisi.\n\n"
    );


    // ============================================================
    // DIRECTORY
    // ============================================================

    create_directory_if_not_exists(
        LOG_FOLDER
    );

    create_directory_if_not_exists(
        LIVE_FOLDER
    );


    // ============================================================
    // REGISTER CARD
    // ============================================================

    card = WD_Register_Card(
        card_type,
        cardnum
    );


    if (card < 0)
    {
        printf(
            "ERROR: WD_Register_Card gagal. "
            "Kode = %d\n",
            card
        );

        return 1;
    }


    printf(
        "PCI-9846H berhasil diregister. Card ID = %d\n",
        card
    );


    // ============================================================
    // GET DEVICE PROPERTIES
    // ============================================================

    DAS_IOT_DEV_PROP cardProp;

    err = WD_GetDeviceProperties(
        card,
        0,
        &cardProp
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_GetDeviceProperties",
            err
        );
    }


    range = cardProp.default_range;


    printf(
        "Default AI range = %u\n",
        range
    );


    // ============================================================
    // CONFIGURE CHANNEL
    // ============================================================

    err = WD_AI_CH_Config(
        card,
        -1,
        range
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_CH_Config",
            err
        );
    }


    // ============================================================
    // CONFIGURE AI
    // ============================================================

    err = WD_AI_Config(
        card,

        WD_IntTimeBase,

        1,

        WD_AI_ADCONVSRC_TimePacer,

        0,

        1
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_Config",
            err
        );
    }


    // ============================================================
    // SAMPLE INTERVAL
    //
    // PCI-9846H:
    //
    // 40 MHz timebase
    //
    // 40 MHz / 20 MHz = 2
    // ============================================================

    samp_intrv =
        (U32)(40000000.0 /
              (double)SAMPLE_RATE_HZ);


    if (samp_intrv < 2)
        samp_intrv = 2;


    printf(
        "Sample interval = %lu\n",
        (unsigned long)samp_intrv
    );


    // ============================================================
    // EVENT SIZE
    // ============================================================

    samples_per_buffer =
        BUFFER_SAMPLES *
        CHANNEL_COUNT;


    event_size_bytes =
        sizeof(U16) *
        (size_t)samples_per_buffer;


    printf(
        "Samples total/event = %lu U16\n",
        (unsigned long)samples_per_buffer
    );

    printf(
        "Event size          = %zu bytes\n",
        event_size_bytes
    );


    // ============================================================
    // CHANNEL LIST
    //
    // IMPORTANT:
    //
    // CH0
    // CH2
    //
    // Output:
    //
    // CH0, CH2,
    // CH0, CH2,
    // CH0, CH2,
    // ...
    // ============================================================

    printf(
        "\nChannel configuration:\n"
        "  Channel 0 : CH0\n"
        "  Channel 1 : CH2\n"
        "  Interleaved data: CH0, CH2, CH0, CH2...\n"
    );


    // ============================================================
    // TRIGGER CONFIGURATION
    //
    // POST TRIGGER
    // EXTERNAL DIGITAL TRIGGER
    // NEGATIVE EDGE
    //
    // TrgCnt = 1
    //
    // Dalam restart mode, continuous acquisition akan melakukan
    // restart acquisition berikutnya secara otomatis.
    // ============================================================

    printf(
        "\nConfiguring external trigger...\n"
    );


    err = WD_AI_Trig_Config(
        card,

        WD_AI_TRGMOD_POST,

        WD_AI_TRGSRC_ExtD,

        WD_AI_TrgNegative,

        0,

        0.0,

        0,

        0,

        0,

        1
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_Trig_Config",
            err
        );
    }


    printf(
        "Trigger : External Digital\n"
        "Edge    : Negative\n"
        "Mode    : Post Trigger\n"
    );


    // ============================================================
    // ENABLE RESTART MODE
    //
    // RestartEn:
    //     continuous AI restart enabled
    //
    // DualBufEn:
    //     dual-buffer restart mode
    //
    // Iter = 0:
    //     infinite restart
    //
    // PCI-9846H mendukung mode ini.
    // ============================================================

    printf(
        "\nEnabling restart continuous AI mode...\n"
    );


    err = WD_AI_Set_Mode(
        card,

        RestartEn |
        DualBufEn,

        0
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_Set_Mode(RestartEn | DualBufEn)",
            err
        );
    }


    printf(
        "Restart mode : ENABLED\n"
        "Dual buffer  : ENABLED\n"
        "Iterations   : INFINITE\n"
    );


    // ============================================================
    // RESET BUFFER
    //
    // HANYA SEKALI.
    //
    // Tidak dilakukan lagi setiap trigger.
    // ============================================================

    err = WD_AI_ContBufferReset(
        card
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_ContBufferReset",
            err
        );
    }


    // ============================================================
    // SETUP BUFFER 1
    // ============================================================

    err = WD_AI_ContBufferSetup(
        card,

        ai_buf,

        samples_per_buffer,

        &Id1
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_ContBufferSetup(buffer 1)",
            err
        );
    }


    // ============================================================
    // SETUP BUFFER 2
    // ============================================================

    err = WD_AI_ContBufferSetup(
        card,

        ai_buf2,

        samples_per_buffer,

        &Id2
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_ContBufferSetup(buffer 2)",
            err
        );
    }


    printf(
        "\n"
        "Buffer setup:\n"
        "  Buffer 1 ID = %d\n"
        "  Buffer 2 ID = %d\n"
        "  Samples     = %lu U16\n"
        "  Size        = %zu bytes\n",
        Id1,
        Id2,
        (unsigned long)samples_per_buffer,
        event_size_bytes
    );


    // ============================================================
    // START CONTINUOUS MULTI CHANNEL ACQUISITION
    //
    // ReadScans:
    //     20.000 sample/channel
    //
    // Channel:
    //     CH0 + CH2
    //
    // Karena PCI-9846H merupakan simultaneous ADC,
    // SampIntrv tidak mempunyai fungsi menurut dokumentasi.
    // ============================================================

    printf(
        "\nStarting acquisition...\n"
    );


    err = WD_AI_ContReadMultiChannels(
        card,

        CHANNEL_COUNT,

        ch_list,

        Id1,

        BUFFER_SAMPLES,

        samp_intrv,

        samp_intrv,

        ASYNCH_OP
    );


    if (err != 0)
    {
        print_error_and_cleanup(
            "WD_AI_ContReadMultiChannels",
            err
        );
    }


    printf(
        "\n"
        "============================================================\n"
        "ACQUISITION RUNNING\n"
        "Waiting for external trigger...\n"
        "============================================================\n"
    );


    // ============================================================
    // EVENT LOOP
    // ============================================================

    while (!exit_now)
    {
        BOOLEAN daq_ready = FALSE;

        BOOLEAN stop_flag = FALSE;

        U16 ready_buffer = 0;


        // --------------------------------------------------------
        // CHECK RESTART READY
        //
        // PCI-9846H menggunakan:
        //
        // WD_AI_AsyncReStartNextReady
        //
        // BUKAN:
        //
        // WD_AI_AsyncReTrigNextReady
        // --------------------------------------------------------

        err = WD_AI_AsyncReStartNextReady(
            card,

            &daq_ready,

            &stop_flag,

            &ready_buffer
        );


        if (err != 0)
        {
            print_error_and_cleanup(
                "WD_AI_AsyncReStartNextReady",
                err
            );
        }


        // --------------------------------------------------------
        // ESC CHECK
        // --------------------------------------------------------

        if (_kbhit())
        {
            int key = _getch();

            if (key == 27)
            {
                printf(
                    "\nESC detected. "
                    "Stopping acquisition...\n"
                );

                exit_now = 1;

                break;
            }
        }


        // --------------------------------------------------------
        // Jika operation berhenti
        // --------------------------------------------------------

        if (stop_flag)
        {
            printf(
                "\nWARNING: DAQ stop flag aktif.\n"
            );

            break;
        }


        // --------------------------------------------------------
        // BELUM ADA DATA
        // --------------------------------------------------------

        if (!daq_ready)
        {
            Sleep(1);

            continue;
        }


        // --------------------------------------------------------
        // DATA READY
        // --------------------------------------------------------

        event_count++;


        printf(
            "\n"
            "------------------------------------------------------------\n"
            "EVENT %lu READY\n"
            "------------------------------------------------------------\n",
            event_count
        );


        // --------------------------------------------------------
        // Tentukan buffer yang berisi event terakhir
        //
        // Pada infinite restart:
        //
        // RdyDaqCnt = index buffer yang menyimpan data terbaru.
        // --------------------------------------------------------

        U16* source_buffer = NULL;


        if (ready_buffer == 0)
        {
            source_buffer = ai_buf;
        }
        else
        {
            source_buffer = ai_buf2;
        }


        // --------------------------------------------------------
        // Validasi index
        //
        // Untuk dua buffer biasanya 0 / 1.
        // --------------------------------------------------------

        if (ready_buffer > 1)
        {
            printf(
                "ERROR: Buffer index tidak valid: %u\n",
                ready_buffer
            );

            break;
        }


        // --------------------------------------------------------
        // Alokasi memory untuk satu event
        //
        // Jangan menyimpan pointer langsung ke ai_buf/ai_buf2
        // karena buffer tersebut akan digunakan kembali hardware.
        // --------------------------------------------------------

        void* event_data =
            malloc(event_size_bytes);


        if (event_data == NULL)
        {
            printf(
                "ERROR: malloc event gagal. "
                "Size = %zu bytes\n",
                event_size_bytes
            );

            break;
        }


        // --------------------------------------------------------
        // Copy hardware buffer
        // --------------------------------------------------------

        memcpy(
            event_data,

            source_buffer,

            event_size_bytes
        );


        // --------------------------------------------------------
        // SAVE LIVE FILE
        // --------------------------------------------------------

        if (!save_live_event(
                event_data,
                event_size_bytes
            ))
        {
            printf(
                "WARNING: Live file gagal disimpan.\n"
            );
        }
        else
        {
            printf(
                "Live file updated: %s\\%s\n",
                LIVE_FOLDER,
                LIVE_UI_FILENAME
            );
        }


        // --------------------------------------------------------
        // Masukkan event ke batch
        // --------------------------------------------------------

        if (g_buffered_count <
            MAX_EVENT_BATCH)
        {
            g_data_buffer[
                g_buffered_count
            ].data = event_data;


            g_data_buffer[
                g_buffered_count
            ].size = event_size_bytes;


            g_buffered_count++;
        }
        else
        {
            // Safety
            free(event_data);

            event_data = NULL;
        }


        printf(
            "Event size     : %zu bytes\n",
            event_size_bytes
        );

        printf(
            "Ready buffer   : %u\n",
            ready_buffer
        );

        printf(
            "Batch progress : %d / %d\n",
            g_buffered_count,
            MAX_EVENT_BATCH
        );


        // --------------------------------------------------------
        // Jika batch sudah 1000 event
        // --------------------------------------------------------

        if (g_buffered_count >=
            MAX_EVENT_BATCH)
        {
            printf(
                "\n"
                "============================================================\n"
                "1000 EVENT REACHED\n"
                "Saving batch...\n"
                "============================================================\n"
            );

            save_batch_to_file();
        }


        // --------------------------------------------------------
        // Jangan melakukan:
        //
        // WD_AI_AsyncClear()
        //
        // di sini.
        //
        // Restart continuous acquisition tetap berjalan.
        // --------------------------------------------------------

        printf(
            "Waiting for next external trigger...\n"
        );
    }


    // ============================================================
    // STOP / CLEANUP
    // ============================================================

    printf(
        "\n"
        "============================================================\n"
        "STOPPING ACQUISITION\n"
        "============================================================\n"
    );


    // ------------------------------------------------------------
    // Stop asynchronous AI
    // ------------------------------------------------------------

    if (card >= 0)
    {
        err = WD_AI_AsyncClear(
            card,
            NULL,
            NULL
        );

        if (err != 0)
        {
            printf(
                "WARNING: WD_AI_AsyncClear returned %d\n",
                err
            );
        }
    }


    // ------------------------------------------------------------
    // Simpan sisa event
    // ------------------------------------------------------------

    if (g_buffered_count > 0)
    {
        printf(
            "\nMenyimpan sisa %d event...\n",
            g_buffered_count
        );

        save_batch_to_file();
    }


    // ------------------------------------------------------------
    // Reset buffer
    // ------------------------------------------------------------

    if (card >= 0)
    {
        WD_AI_ContBufferReset(card);
    }


    // ------------------------------------------------------------
    // Release card
    // ------------------------------------------------------------

    if (card >= 0)
    {
        WD_Release_Card(card);

        card = -1;
    }


    printf(
        "\n"
        "============================================================\n"
        "PROGRAM SELESAI\n"
        "============================================================\n"
    );

    printf(
        "Total event acquired : %lu\n",
        event_count
    );

    printf(
        "\nTekan tombol apa saja untuk keluar..."
    );

    _getch();


    return 0;
}