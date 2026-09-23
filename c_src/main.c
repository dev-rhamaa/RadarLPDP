#define BUILDING_DAQ_DLL
#include "main.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "wd-dask.h"
#include "wddaskex.h"

/* ================================================================
 * Internal Global State
 * ================================================================ */
static int16_t  g_card = -1;
static uint16_t g_card_num = DEFAULT_CARD_NUM;
static uint32_t g_sample_rate = DEFAULT_SAMPLE_RATE_HZ;
static uint32_t g_buffer_samples = DEFAULT_BUFFER_SAMPLES;
static uint32_t g_samples_per_buffer = 0;
static uint32_t g_samp_intrv = 2;

/* Hardware DMA double buffers */
static uint16_t* g_ai_buf1 = NULL;
static uint16_t* g_ai_buf2 = NULL;
static int16_t   g_id1 = -1;
static int16_t   g_id2 = -1;

/* Internal de-interleaved channel buffers (Zero-Copy target for Python) */
static uint16_t* g_ch0_data = NULL;
static uint16_t* g_ch2_data = NULL;

static uint32_t g_event_count = 0;
static int      g_is_active = 0;


/* ================================================================
 * API Implementation
 * ================================================================ */

DAQ_API int daq_init(uint16_t card_num, uint32_t sample_rate, uint32_t buffer_samples)
{
    I16 err;
    DAS_IOT_DEV_PROP card_prop;
    U16 ai_range = 0;

    if (g_card >= 0)
    {
        /* Card already initialized */
        return 0;
    }

    g_card_num = card_num;
    g_sample_rate = (sample_rate > 0) ? sample_rate : DEFAULT_SAMPLE_RATE_HZ;
    g_buffer_samples = (buffer_samples > 0) ? buffer_samples : DEFAULT_BUFFER_SAMPLES;
    g_samples_per_buffer = g_buffer_samples * DAQ_CHANNEL_COUNT;
    g_event_count = 0;

    /* 1. Register Card ADLink PCI-9846H */
    g_card = WD_Register_Card(DEFAULT_CARD_TYPE, g_card_num);
    if (g_card < 0)
    {
        return (int)g_card; /* Return ADLink negative error code */
    }

    /* 2. Allocate RAM buffers */
    g_ai_buf1 = (uint16_t*)calloc(g_samples_per_buffer, sizeof(uint16_t));
    g_ai_buf2 = (uint16_t*)calloc(g_samples_per_buffer, sizeof(uint16_t));
    g_ch0_data = (uint16_t*)calloc(g_buffer_samples, sizeof(uint16_t));
    g_ch2_data = (uint16_t*)calloc(g_buffer_samples, sizeof(uint16_t));

    if (!g_ai_buf1 || !g_ai_buf2 || !g_ch0_data || !g_ch2_data)
    {
        daq_release();
        return -100; /* Allocation failure */
    }

    /* 3. Query Device Properties & Range */
    memset(&card_prop, 0, sizeof(card_prop));
    err = WD_GetDeviceProperties((U16)g_card, 0, &card_prop);
    if (err == 0)
    {
        ai_range = (U16)card_prop.default_range;
    }

    /* 4. Configure Channel & AI TimeBase */
    err = WD_AI_CH_Config((U16)g_card, -1, ai_range);
    if (err != 0)
    {
        daq_release();
        return (int)err;
    }

    err = WD_AI_Config((U16)g_card, WD_IntTimeBase, 1, WD_AI_ADCONVSRC_TimePacer, 0, 1);
    if (err != 0)
    {
        daq_release();
        return (int)err;
    }

    /* 5. Calculate Sample Interval (40 MHz timebase / sample_rate) */
    g_samp_intrv = (uint32_t)(40000000.0 / (double)g_sample_rate);
    if (g_samp_intrv < 2)
    {
        g_samp_intrv = 2;
    }

    /* 6. Configure External Digital Trigger (Negative edge, Post Trigger) */
    err = WD_AI_Trig_Config(
        (U16)g_card,
        WD_AI_TRGMOD_POST,
        WD_AI_TRGSRC_ExtD,
        WD_AI_TrgNegative,
        0, 0.0, 0, 0, 0, 1
    );
    if (err != 0)
    {
        daq_release();
        return (int)err;
    }

    /* 7. Enable Continuous Restart Mode (RestartEn | DualBufEn) */
    err = WD_AI_Set_Mode((U16)g_card, RestartEn | DualBufEn, 0);
    if (err != 0)
    {
        daq_release();
        return (int)err;
    }

    /* 8. Setup Double Buffers */
    WD_AI_ContBufferReset((U16)g_card);

    g_id1 = -1;
    g_id2 = -1;
    err = WD_AI_ContBufferSetup((U16)g_card, g_ai_buf1, g_samples_per_buffer, &g_id1);
    if (err != 0)
    {
        daq_release();
        return (int)err;
    }

    err = WD_AI_ContBufferSetup((U16)g_card, g_ai_buf2, g_samples_per_buffer, &g_id2);
    if (err != 0)
    {
        daq_release();
        return (int)err;
    }

    return 0;
}


DAQ_API int daq_start(void)
{
    I16 err;
    U16 ch_list[DAQ_CHANNEL_COUNT] = { 0, 2 };

    if (g_card < 0)
    {
        return -1;
    }

    if (g_is_active)
    {
        return 0;
    }

    err = WD_AI_ContReadMultiChannels(
        (U16)g_card,
        DAQ_CHANNEL_COUNT,
        ch_list,
        (U16)g_id1,
        g_buffer_samples,
        g_samp_intrv,
        g_samp_intrv,
        ASYNCH_OP
    );

    if (err == 0)
    {
        g_is_active = 1;
    }

    return (int)err;
}


DAQ_API int daq_poll_event(int* is_ready, uint16_t* ready_buffer_idx)
{
    I16 err;
    BOOLEAN b_ready = FALSE;
    BOOLEAN stop_flag = FALSE;
    U16 ready_buf = 0;

    if (g_card < 0 || !g_is_active)
    {
        if (is_ready) *is_ready = 0;
        return -1;
    }

    err = WD_AI_AsyncReStartNextReady((U16)g_card, &b_ready, &stop_flag, &ready_buf);
    if (err != 0)
    {
        if (is_ready) *is_ready = 0;
        return (int)err;
    }

    if (stop_flag)
    {
        g_is_active = 0;
        if (is_ready) *is_ready = 0;
        return -2; /* Hardware stop flag triggered */
    }

    if (is_ready)
    {
        *is_ready = b_ready ? 1 : 0;
    }

    if (ready_buffer_idx && b_ready)
    {
        *ready_buffer_idx = ready_buf;
    }

    return 0;
}


DAQ_API int daq_read_channels(uint16_t* ch0_dest, uint16_t* ch2_dest, uint32_t max_samples)
{
    int is_ready = 0;
    uint16_t ready_idx = 0;
    uint16_t* src = NULL;
    uint32_t i;
    uint32_t copy_count;

    if (g_card < 0 || !g_is_active || !ch0_dest || !ch2_dest)
    {
        return -1;
    }

    if (daq_poll_event(&is_ready, &ready_idx) != 0 || !is_ready)
    {
        return 0; /* No new trigger event yet */
    }

    src = (ready_idx == 0) ? g_ai_buf1 : g_ai_buf2;
    copy_count = (max_samples < g_buffer_samples) ? max_samples : g_buffer_samples;

    /* De-interleave CH0 and CH2 directly into destination buffers */
    for (i = 0; i < copy_count; i++)
    {
        ch0_dest[i] = src[2 * i];
        ch2_dest[i] = src[2 * i + 1];
    }

    g_event_count++;
    return (int)copy_count;
}


DAQ_API int daq_get_channel_pointers(const uint16_t** ch0_ptr, const uint16_t** ch2_ptr, uint32_t* sample_count)
{
    int is_ready = 0;
    uint16_t ready_idx = 0;
    uint16_t* src = NULL;
    uint32_t i;

    if (g_card < 0 || !g_is_active || !ch0_ptr || !ch2_ptr || !sample_count)
    {
        return -1;
    }

    if (daq_poll_event(&is_ready, &ready_idx) != 0 || !is_ready)
    {
        return 0; /* No new trigger event */
    }

    src = (ready_idx == 0) ? g_ai_buf1 : g_ai_buf2;

    /* De-interleave into internal contiguous arrays */
    for (i = 0; i < g_buffer_samples; i++)
    {
        g_ch0_data[i] = src[2 * i];
        g_ch2_data[i] = src[2 * i + 1];
    }

    *ch0_ptr = g_ch0_data;
    *ch2_ptr = g_ch2_data;
    *sample_count = g_buffer_samples;

    g_event_count++;
    return 1; /* New event available */
}


DAQ_API int daq_stop(void)
{
    U32 start_pos = 0;
    U32 access_cnt = 0;

    if (g_card >= 0)
    {
        WD_AI_AsyncClear((U16)g_card, &start_pos, &access_cnt);
        WD_AI_ContBufferReset((U16)g_card);
    }

    g_is_active = 0;
    return 0;
}


DAQ_API void daq_release(void)
{
    daq_stop();

    if (g_card >= 0)
    {
        WD_Release_Card((U16)g_card);
        g_card = -1;
    }

    if (g_ai_buf1)  { free(g_ai_buf1);  g_ai_buf1 = NULL; }
    if (g_ai_buf2)  { free(g_ai_buf2);  g_ai_buf2 = NULL; }
    if (g_ch0_data) { free(g_ch0_data); g_ch0_data = NULL; }
    if (g_ch2_data) { free(g_ch2_data); g_ch2_data = NULL; }

    g_id1 = -1;
    g_id2 = -1;
    g_is_active = 0;
}


DAQ_API uint32_t daq_get_event_count(void)
{
    return g_event_count;
}


DAQ_API int daq_is_active(void)
{
    return g_is_active;
}
