"""C-Embedded Data Acquisition & Hardware Control Module.

This module ports the continuous restart DMA acquisition and batch logging logic
from 'Legacy C Code/cadgetdatanew.c' directly into Python using ctypes and ADLink's
wd-dask64.dll.

Features:
- Native 64-bit ctypes bindings to WD-Dask API for PCI-9846H DAQ card.
- Continuous multi-channel simultaneous acquisition (CH0, CH2).
- Zero-disk streaming directly to Python memory queues (ultra-low latency).
- Auto batch logging (1000 events) to log/ directory matching exact C format.
- Standby / simulation fallback mode when hardware card is not present.
"""

import ctypes
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any
import numpy as np

from config import (
    SAMPLE_RATE as DEFAULT_SAMPLE_RATE_HZ,
    BUFFER_SAMPLES as DEFAULT_BUFFER_SAMPLES,
    FILENAME as DEFAULT_LIVE_FILENAME,
    C_DAQ_ENABLED as DEFAULT_C_DAQ_ENABLED,
    C_DAQ_WRITE_LIVE_BIN as DEFAULT_WRITE_LIVE_BIN,
    C_DAQ_BATCH_LOG_ENABLED as DEFAULT_BATCH_LOG_ENABLED,
    C_DAQ_BATCH_MAX_EVENTS as DEFAULT_BATCH_MAX_EVENTS,
)

# Type definitions matching ADLink Wd-dask.h
U8 = ctypes.c_uint8
I16 = ctypes.c_int16
U16 = ctypes.c_uint16
I32 = ctypes.c_int32
U32 = ctypes.c_uint32
F32 = ctypes.c_float
F64 = ctypes.c_double
BOOLEAN = ctypes.c_bool

# Hardware & Acquisition Constants from cadgetdatanew.c
PCI_9846H = 0x17
CARD_NUM = 0

CHANNEL_COUNT = 2               # CH0 and CH2
SELECTED_CHANNELS = (0, 2)
SAMPLE_RATE_HZ = DEFAULT_SAMPLE_RATE_HZ
BUFFER_SAMPLES = DEFAULT_BUFFER_SAMPLES
MAX_EVENT_BATCH = DEFAULT_BATCH_MAX_EVENTS

# DAQ Operation, Mode & Trigger Constants
WD_IntTimeBase = 0x3
WD_AI_ADCONVSRC_TimePacer = 0
WD_AI_TRGMOD_POST = 0x00
WD_AI_TRGSRC_ExtD = 0x02
WD_AI_TrgNegative = 0x0
ASYNCH_OP = 1

# Advanced DAQ Mode flags
RestartEn = 0x2
DualBufEn = 0x4


# Device property structure matching wddaskex.h
class DasIotDevProp(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("card_type", I16),
        ("num_of_channel", I16),
        ("data_width", I16),
        ("default_range", I16),
        ("ctrKHz", U32),
        ("bdbase", U32),
        ("mask", U32),
        ("reserved", U32 * 15),
    ]


class DaskDriver:
    """ctypes interface to ADLink wd-dask64.dll / WD-Dask.dll."""

    def __init__(self, dll_path: Optional[str] = None):
        self.dll: Optional[ctypes.WinDLL] = None
        self.is_available: bool = False
        self.dll_path: Optional[str] = None
        self._load_library(dll_path)

    def _load_library(self, explicit_path: Optional[str] = None):
        if sys.platform != "win32":
            return

        candidates = []
        if explicit_path:
            candidates.append(explicit_path)

        project_root = Path(__file__).resolve().parent.parent

        # Prioritize 64-bit DLL from c_src/lib if on 64-bit Python
        if sys.maxsize > 2**32:
            candidates.extend([
                str(project_root / "c_src" / "lib" / "wd-dask64.dll"),
                str(project_root / "bin" / "wd-dask64.dll"),
                "wd-dask64.dll",
                "WD-Dask64.dll",
            ])
        else:
            candidates.extend([
                str(project_root / "c_src" / "lib" / "WD-Dask.dll"),
                "WD-Dask.dll",
            ])

        for path_str in candidates:
            if not path_str:
                continue
            try:
                self.dll = ctypes.WinDLL(path_str)
                self.dll_path = path_str
                self._bind_functions()
                self.is_available = True
                print(f"[c_acquisition] Berhasil memuat library DAQ: {path_str}")
                break
            except (OSError, FileNotFoundError):
                continue

    def _bind_functions(self):
        """Bind C prototypes matching Wd-dask64.h & cadgetdatanew.c."""
        if not self.dll:
            return

        # I16 WD_Register_Card(U16 CardType, U16 card_num)
        self.WD_Register_Card = self.dll.WD_Register_Card
        self.WD_Register_Card.argtypes = [U16, U16]
        self.WD_Register_Card.restype = I16

        # I16 WD_Release_Card(U16 CardNumber)
        self.WD_Release_Card = self.dll.WD_Release_Card
        self.WD_Release_Card.argtypes = [U16]
        self.WD_Release_Card.restype = I16

        # I16 WD_GetDeviceProperties(U16 wCardNumber, U16 type, DAS_IOT_DEV_PROP* cardProp)
        if hasattr(self.dll, "WD_GetDeviceProperties"):
            self.WD_GetDeviceProperties = self.dll.WD_GetDeviceProperties
            self.WD_GetDeviceProperties.argtypes = [U16, U16, ctypes.POINTER(DasIotDevProp)]
            self.WD_GetDeviceProperties.restype = I16

        # I16 WD_AI_CH_Config(U16 CardNumber, I16 Channel, U16 AdRange)
        self.WD_AI_CH_Config = self.dll.WD_AI_CH_Config
        self.WD_AI_CH_Config.argtypes = [U16, I16, U16]
        self.WD_AI_CH_Config.restype = I16

        # I16 WD_AI_Config(U16 CardNumber, U16 TimeBase, BOOLEAN adDutyRestore, U16 ConvSrc, BOOLEAN doubleEdged, BOOLEAN AutoResetBuf)
        self.WD_AI_Config = self.dll.WD_AI_Config
        self.WD_AI_Config.argtypes = [U16, U16, BOOLEAN, U16, BOOLEAN, BOOLEAN]
        self.WD_AI_Config.restype = I16

        # I16 WD_AI_Trig_Config(U16 wCardNumber, U16 trigMode, U16 trigSrc, U16 trigPol, U16 anaTrigchan, F64 anaTriglevel, U32 postTrigScans, U32 preTrigScans, U32 trigDelayTicks, U32 reTrgCnt)
        self.WD_AI_Trig_Config = self.dll.WD_AI_Trig_Config
        self.WD_AI_Trig_Config.argtypes = [U16, U16, U16, U16, U16, F64, U32, U32, U32, U32]
        self.WD_AI_Trig_Config.restype = I16

        # I16 WD_AI_Set_Mode(U16 wCardNumber, U16 modeCtrl, U16 wIter)
        self.WD_AI_Set_Mode = self.dll.WD_AI_Set_Mode
        self.WD_AI_Set_Mode.argtypes = [U16, U16, U16]
        self.WD_AI_Set_Mode.restype = I16

        # I16 WD_AI_ContBufferReset(U16 wCardNumber)
        self.WD_AI_ContBufferReset = self.dll.WD_AI_ContBufferReset
        self.WD_AI_ContBufferReset.argtypes = [U16]
        self.WD_AI_ContBufferReset.restype = I16

        # I16 WD_AI_ContBufferSetup(U16 wCardNumber, void *pwBuffer, U32 dwReadCount, U16 *BufferId)
        self.WD_AI_ContBufferSetup = self.dll.WD_AI_ContBufferSetup
        self.WD_AI_ContBufferSetup.argtypes = [U16, ctypes.c_void_p, U32, ctypes.POINTER(I16)]
        self.WD_AI_ContBufferSetup.restype = I16

        # I16 WD_AI_ContReadMultiChannels(U16 CardNumber, U16 NumChans, U16 *Chans, U16 BufId, U32 ReadScans, U32 ScanIntrv, U32 SampIntrv, U16 SyncMode)
        self.WD_AI_ContReadMultiChannels = self.dll.WD_AI_ContReadMultiChannels
        self.WD_AI_ContReadMultiChannels.argtypes = [U16, U16, ctypes.POINTER(U16), U16, U32, U32, U32, U16]
        self.WD_AI_ContReadMultiChannels.restype = I16

        # I16 WD_AI_AsyncReStartNextReady(U16 wCardNumber, BOOLEAN *bReady, BOOLEAN *StopFlag, U16 *RdyDaqCnt)
        self.WD_AI_AsyncReStartNextReady = self.dll.WD_AI_AsyncReStartNextReady
        self.WD_AI_AsyncReStartNextReady.argtypes = [U16, ctypes.POINTER(BOOLEAN), ctypes.POINTER(BOOLEAN), ctypes.POINTER(U16)]
        self.WD_AI_AsyncReStartNextReady.restype = I16

        # I16 WD_AI_AsyncClear(U16 CardNumber, U32 *StartPos, U32 *AccessCnt)
        self.WD_AI_AsyncClear = self.dll.WD_AI_AsyncClear
        self.WD_AI_AsyncClear.argtypes = [U16, ctypes.POINTER(U32), ctypes.POINTER(U32)]
        self.WD_AI_AsyncClear.restype = I16


class NativeCAcquisitionEngine:
    """High-performance acquisition engine matching cadgetdatanew.c logic."""

    def __init__(
        self,
        sample_rate_hz: int = DEFAULT_SAMPLE_RATE_HZ,
        buffer_samples: int = DEFAULT_BUFFER_SAMPLES,
        channels: Tuple[int, int] = SELECTED_CHANNELS,
        log_folder: str = "log",
        live_file: str = DEFAULT_LIVE_FILENAME,
        enabled: bool = DEFAULT_C_DAQ_ENABLED,
        write_live_bin: bool = DEFAULT_WRITE_LIVE_BIN,
        batch_log_enabled: bool = DEFAULT_BATCH_LOG_ENABLED,
        batch_max_events: int = DEFAULT_BATCH_MAX_EVENTS,
        on_event_received: Optional[Callable[[np.ndarray, np.ndarray, int], None]] = None
    ):
        self.sample_rate_hz = sample_rate_hz
        self.buffer_samples = buffer_samples
        self.channels = channels
        self.channel_count = len(channels)
        self.samples_per_buffer = self.buffer_samples * self.channel_count
        self.event_size_bytes = self.samples_per_buffer * ctypes.sizeof(U16)
        self.log_folder = log_folder
        self.live_file = live_file
        self.enabled = enabled
        self.write_live_bin = write_live_bin
        self.batch_log_enabled = batch_log_enabled
        self.batch_max_events = batch_max_events
        self.on_event_received = on_event_received

        self.driver = DaskDriver()
        self.card_id: int = -1
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Batch logging state
        self.batch_buffer: List[bytes] = []
        self.event_count: int = 0
        if self.batch_log_enabled:
            os.makedirs(self.log_folder, exist_ok=True)

    def is_hardware_available(self) -> bool:
        """Check if driver is loaded and DAQ card registers successfully."""
        if not self.driver.is_available:
            return False
        test_id = self.driver.WD_Register_Card(PCI_9846H, CARD_NUM)
        if test_id >= 0:
            self.driver.WD_Release_Card(test_id)
            return True
        return False

    def start(self) -> bool:
        """Start the background acquisition thread."""
        if self._thread and self._thread.is_alive():
            return True

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_acquisition_loop,
            daemon=True,
            name="CDaqAcquisitionWorker"
        )
        self._thread.start()
        return True

    def stop(self):
        """Stop acquisition and release DAQ hardware gracefully."""
        self._stop_event.set()
        if (
            self._thread
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=2.0)
            self._thread = None

        if self.card_id >= 0 and self.driver.is_available:
            try:
                start_pos = U32(0)
                access_cnt = U32(0)
                self.driver.WD_AI_AsyncClear(
                    self.card_id,
                    ctypes.byref(start_pos),
                    ctypes.byref(access_cnt)
                )
                self.driver.WD_AI_ContBufferReset(self.card_id)
                self.driver.WD_Release_Card(self.card_id)
                print(f"[c_acquisition] Kartu DAQ (ID: {self.card_id}) berhasil dilepaskan.")
            except Exception as e:
                print(f"[c_acquisition] Error saat release kartu: {e}")
            finally:
                self.card_id = -1

        # Flush any remaining batch logs on shutdown
        if self.batch_log_enabled and self.batch_buffer:
            self._save_batch_to_file()

    def _save_live_event(self, raw_bytes: bytes) -> None:
        """Save latest buffer to live .bin file atomically for analytics compatibility."""
        try:
            live_path = Path(self.live_file)
            live_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = live_path.with_suffix(".tmp")

            with open(tmp_path, "wb") as f:
                f.write(raw_bytes)

            tmp_path.replace(live_path)
        except Exception:
            pass

    def _save_batch_to_file(self):
        """Save accumulated event batch with metadata header matching cadgetdatanew.c."""
        if not self.batch_buffer:
            return

        events_to_save = len(self.batch_buffer)
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        log_filepath = Path(self.log_folder) / f"batch_log_{timestamp_str}_{events_to_save:04d}_evt.bin"

        header_lines = [
            f"TEST_DATE:{now.strftime('%Y-%m-%d %H:%M:%S')}",
            "CODE_VERSION:Code trigger V.4 (Python Native C-Embedded)",
            "AUTHOR:Raihan Muhammad",
            "CARD:PCI-9846H",
            f"CHANNEL_COUNT:{self.channel_count}",
            f"CHANNELS:CH{self.channels[0]},CH{self.channels[1]}",
            f"SAMPLE_RATE:{self.sample_rate_hz}",
            f"SAMPLES_PER_CHANNEL:{self.buffer_samples}",
            f"EVENT_DATA_FORMAT:CH{self.channels[0]},CH{self.channels[1]}_INTERLEAVED",
            f"EVENT_SIZE_BYTES:{self.event_size_bytes}",
            f"BATCH_EVENT_COUNT:{events_to_save}",
            "\n"
        ]
        header_bytes = "\n".join(header_lines).encode("utf-8")

        try:
            with open(log_filepath, "wb") as f_log:
                f_log.write(header_bytes)
                for raw_event in self.batch_buffer:
                    f_log.write(raw_event)
            print(f"[c_acquisition] Batch log ({events_to_save} events) disimpan ke {log_filepath}")
        except Exception as e:
            print(f"[c_acquisition] Gagal menulis batch log file: {e}")
        finally:
            self.batch_buffer.clear()

    def _run_acquisition_loop(self):
        """Worker thread executing the continuous DMA restart acquisition."""
        if not self.enabled:
            print("[c_acquisition] Native C DAQ engine dinonaktifkan dalam config.")
            return

        if not self.driver.is_available:
            print("[c_acquisition] Driver WD-Dask tidak terdeteksi. Standby.")
            return

        print("[c_acquisition] Menginisialisasi kartu ADLink PCI-9846H...")
        self.card_id = self.driver.WD_Register_Card(PCI_9846H, CARD_NUM)
        if self.card_id < 0:
            print(f"[c_acquisition] Gagal registrasi kartu ADLink (kode={self.card_id}). Memasuki mode standby.")
            return

        try:
            # 1. Get Device Properties & Range
            card_prop = DasIotDevProp()
            err = self.driver.WD_GetDeviceProperties(self.card_id, 0, ctypes.byref(card_prop))
            ai_range = card_prop.default_range if err == 0 else 0

            # 2. Configure Channel & AI
            self.driver.WD_AI_CH_Config(self.card_id, -1, ai_range)
            self.driver.WD_AI_Config(self.card_id, WD_IntTimeBase, True, WD_AI_ADCONVSRC_TimePacer, False, True)

            # 3. Calculate sample interval (40 MHz / 20 MHz = 2)
            samp_intrv = int(40_000_000 / self.sample_rate_hz)
            if samp_intrv < 2:
                samp_intrv = 2

            # 4. Configure External Digital Trigger (Negative edge, Post trigger)
            self.driver.WD_AI_Trig_Config(
                self.card_id,
                WD_AI_TRGMOD_POST,
                WD_AI_TRGSRC_ExtD,
                WD_AI_TrgNegative,
                0, 0.0, 0, 0, 0, 1
            )

            # 5. Enable Continuous Restart Mode (RestartEn | DualBufEn)
            self.driver.WD_AI_Set_Mode(self.card_id, RestartEn | DualBufEn, 0)
            self.driver.WD_AI_ContBufferReset(self.card_id)

            # 6. Allocate DMA Double Buffers
            ai_buf1 = (U16 * self.samples_per_buffer)()
            ai_buf2 = (U16 * self.samples_per_buffer)()
            id1 = I16(-1)
            id2 = I16(-1)

            self.driver.WD_AI_ContBufferSetup(self.card_id, ai_buf1, self.samples_per_buffer, ctypes.byref(id1))
            self.driver.WD_AI_ContBufferSetup(self.card_id, ai_buf2, self.samples_per_buffer, ctypes.byref(id2))

            # 7. Start Simultaneous Multi-Channel Acquisition (CH0, CH2)
            ch_list = (U16 * self.channel_count)(*self.channels)
            err = self.driver.WD_AI_ContReadMultiChannels(
                self.card_id,
                self.channel_count,
                ch_list,
                U16(id1.value),
                self.buffer_samples,
                samp_intrv,
                samp_intrv,
                ASYNCH_OP
            )
            if err != 0:
                print(f"[c_acquisition] Gagal memulai WD_AI_ContReadMultiChannels: {err}")
                return

            print(f"[c_acquisition] Continuous acquisition berjalan pada {self.sample_rate_hz/1e6:.1f} MS/s.")
            print("[c_acquisition] Menunggu external digital trigger...")

            # 8. Main Event Polling Loop
            daq_ready = BOOLEAN(False)
            stop_flag = BOOLEAN(False)
            ready_buffer = U16(0)

            while not self._stop_event.is_set():
                err = self.driver.WD_AI_AsyncReStartNextReady(
                    self.card_id,
                    ctypes.byref(daq_ready),
                    ctypes.byref(stop_flag),
                    ctypes.byref(ready_buffer)
                )

                if err != 0:
                    print(f"[c_acquisition] Error AsyncReStartNextReady: {err}")
                    break

                if stop_flag.value:
                    print("[c_acquisition] DAQ stop flag aktif.")
                    break

                if not daq_ready.value:
                    # Non-blocking sleep 1ms as in cadgetdatanew.c Sleep(1)
                    time.sleep(0.001)
                    continue

                # Buffer ready! Extract active buffer (0 -> ai_buf1, 1 -> ai_buf2)
                self.event_count += 1
                source_buf = ai_buf1 if ready_buffer.value == 0 else ai_buf2

                # Fast zero-copy NumPy array mapping from ctypes DMA buffer
                raw_arr = np.ctypeslib.as_array(source_buf)

                # De-interleave CH0 and CH2 directly into float32 arrays
                ch1 = raw_arr[0::2].astype(np.float32)
                ch2 = raw_arr[1::2].astype(np.float32)

                # Dispatch event directly to in-memory queue for instant UI rendering
                if self.on_event_received:
                    self.on_event_received(ch1, ch2, self.sample_rate_hz)

                # Mirror to live file only if explicitly enabled
                if self.write_live_bin:
                    self._save_live_event(bytes(source_buf))

                # Append to batch logger only if explicitly enabled
                if self.batch_log_enabled:
                    raw_bytes = bytes(source_buf)
                    self.batch_buffer.append(raw_bytes)
                    if len(self.batch_buffer) >= self.batch_max_events:
                        self._save_batch_to_file()

        except Exception as e:
            print(f"[c_acquisition] Exception dalam acquisition loop: {e}")
        finally:
            self.stop()
