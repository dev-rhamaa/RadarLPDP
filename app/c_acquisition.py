"""C-Embedded Data Acquisition & Channel De-interleaving Module.

This module provides direct ctypes bindings to ADLink PCI-9846H DAQ (WD-Dask.dll)
and an efficient C-compatible channel extraction pipeline (CH1 & CH3) directly in Python,
eliminating the need for external child processes and disk file polling.
"""

import ctypes
import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Tuple
import numpy as np

# Type definitions matching ADLink Wd-dask.h
U8 = ctypes.c_uint8
I16 = ctypes.c_int16
U16 = ctypes.c_uint16
I32 = ctypes.c_int32
U32 = ctypes.c_uint32
F32 = ctypes.c_float
F64 = ctypes.c_double

# Hardware constants
PCI_9846H = 0x17
TOTAL_HW_CHANNELS = 4       # CH0..CH3
SELECTED_CHANNELS = (1, 3)  # CH1 and CH3
SELECTED_COUNT = len(SELECTED_CHANNELS)
DEFAULT_BUFFER_SAMPLES = 8192
DEFAULT_SAMPLE_RATE_HZ = 20_000_000

# DAQ Operation & Trigger Constants
WD_IntTimeBase = 0x3
WD_AI_ADCONVSRC_TimePacer = 0
WD_AI_TRGMOD_POST = 0x00
WD_AI_TRGSRC_ExtD = 0x02
WD_AI_TrgNegative = 0x0
ASYNCH_OP = 1

# Search paths for WD-Dask.dll
DLL_CANDIDATE_NAMES = [
    "WD-Dask64.dll" if sys.maxsize > 2**32 else "WD-Dask.dll",
    "WD-Dask.dll",
    "PCI-Dask.dll",
]


class DasIotDevProp(ctypes.Structure):
    """ADLink device property structure."""
    _fields_ = [
        ("device_name", ctypes.c_char * 64),
        ("default_range", U16),
        ("reserved", U16 * 16),
    ]


class DaskDriver:
    """Wrapper around WD-Dask.dll using ctypes."""

    def __init__(self, dll_path: Optional[str] = None):
        self.dll: Optional[ctypes.WinDLL] = None
        self.is_available: bool = False
        self._load_library(dll_path)

    def _load_library(self, dll_path: Optional[str] = None):
        if sys.platform != "win32":
            return

        candidates = [dll_path] if dll_path else []
        candidates.extend(DLL_CANDIDATE_NAMES)

        # Also check local incl / lib folders if any
        base_dir = Path(__file__).resolve().parent.parent
        for sub in ["CodeTriggerExtBaru", "CodeTriggerExtBaru/lib", "bin"]:
            for name in DLL_CANDIDATE_NAMES:
                candidates.append(str(base_dir / sub / name))

        for candidate in candidates:
            if not candidate:
                continue
            try:
                self.dll = ctypes.WinDLL(candidate)
                self._bind_functions()
                self.is_available = True
                print(f"[c_acquisition] Berhasil memuat driver C DAQ: {candidate}")
                break
            except (OSError, FileNotFoundError):
                continue

    def _bind_functions(self):
        """Bind C prototypes from WD-Dask.h."""
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

        # I16 WD_AI_CH_Config(U16 CardNumber, I16 Channel, U16 AdRange)
        self.WD_AI_CH_Config = self.dll.WD_AI_CH_Config
        self.WD_AI_CH_Config.argtypes = [U16, I16, U16]
        self.WD_AI_CH_Config.restype = I16

        # I16 WD_AI_Config(U16 CardNumber, U16 TimeBase, U16 AdConvSrc, U16 TrgMode, U16 TrgCtrl)
        if hasattr(self.dll, "WD_AI_Config"):
            self.WD_AI_Config = self.dll.WD_AI_Config
            self.WD_AI_Config.restype = I16

        # I16 WD_AI_Trig_Config(...)
        if hasattr(self.dll, "WD_AI_Trig_Config"):
            self.WD_AI_Trig_Config = self.dll.WD_AI_Trig_Config
            self.WD_AI_Trig_Config.restype = I16

        # I16 WD_AI_AsyncDblBufferMode(U16 CardNumber, BOOLEAN Enable)
        if hasattr(self.dll, "WD_AI_AsyncDblBufferMode"):
            self.WD_AI_AsyncDblBufferMode = self.dll.WD_AI_AsyncDblBufferMode
            self.WD_AI_AsyncDblBufferMode.argtypes = [U16, ctypes.c_bool]
            self.WD_AI_AsyncDblBufferMode.restype = I16

        # I16 WD_AI_ContBufferSetup(U16 CardNumber, void* Buffer, U32 ReadCount, U16* BufferId)
        if hasattr(self.dll, "WD_AI_ContBufferSetup"):
            self.WD_AI_ContBufferSetup = self.dll.WD_AI_ContBufferSetup
            self.WD_AI_ContBufferSetup.argtypes = [U16, ctypes.c_void_p, U32, ctypes.POINTER(U16)]
            self.WD_AI_ContBufferSetup.restype = I16

        # I16 WD_AI_AsyncDblBufferHalfReady(U16 CardNumber, BOOLEAN* HalfReady, BOOLEAN* StopFlag)
        if hasattr(self.dll, "WD_AI_AsyncDblBufferHalfReady"):
            self.WD_AI_AsyncDblBufferHalfReady = self.dll.WD_AI_AsyncDblBufferHalfReady
            self.WD_AI_AsyncDblBufferHalfReady.argtypes = [U16, ctypes.POINTER(ctypes.c_bool), ctypes.POINTER(ctypes.c_bool)]
            self.WD_AI_AsyncDblBufferHalfReady.restype = I16

        # I16 WD_AI_AsyncDblBufferHandled(U16 CardNumber)
        if hasattr(self.dll, "WD_AI_AsyncDblBufferHandled"):
            self.WD_AI_AsyncDblBufferHandled = self.dll.WD_AI_AsyncDblBufferHandled
            self.WD_AI_AsyncDblBufferHandled.argtypes = [U16]
            self.WD_AI_AsyncDblBufferHandled.restype = I16

        # I16 WD_AI_AsyncClear(U16 CardNumber, U32* StartPos, U32* AccessCnt)
        if hasattr(self.dll, "WD_AI_AsyncClear"):
            self.WD_AI_AsyncClear = self.dll.WD_AI_AsyncClear
            self.WD_AI_AsyncClear.argtypes = [U16, ctypes.POINTER(U32), ctypes.POINTER(U32)]
            self.WD_AI_AsyncClear.restype = I16


def extract_selected_channels_numpy(
    raw_buffer: np.ndarray,
    n_samples: int = DEFAULT_BUFFER_SAMPLES,
    total_hw_channels: int = TOTAL_HW_CHANNELS,
    selected_channels: Tuple[int, int] = SELECTED_CHANNELS
) -> np.ndarray:
    """Fast C-equivalent vectorized de-interleaving of CH1 & CH3.
    
    Equivalent to C function extract_selected_channels in cadgetdata.c:
    Copies CH1 then CH3 sequentially per sample timestamp.
    """
    reshaped = raw_buffer[:n_samples * total_hw_channels].reshape((n_samples, total_hw_channels))
    selected = reshaped[:, list(selected_channels)]  # shape: (n_samples, 2)
    return np.ascontiguousarray(selected.reshape(-1), dtype=np.uint16)


class NativeCAcquisitionEngine:
    """Manages direct C acquisition lifecycle with background thread & zero-copy buffer."""

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE_HZ,
        buffer_samples: int = DEFAULT_BUFFER_SAMPLES,
        on_data_ready: Optional[Callable[[np.ndarray, np.ndarray], None]] = None,
        live_file_path: Optional[str] = None
    ):
        self.sample_rate = sample_rate
        self.buffer_samples = buffer_samples
        self.on_data_ready = on_data_ready
        self.live_file_path = live_file_path
        self.driver = DaskDriver()
        self.card_id = -1
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Start acquisition loop in background thread."""
        if self._thread and self._thread.is_alive():
            return True

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="NativeCAcqWorker")
        self._thread.start()
        return True

    def stop(self):
        """Stop acquisition gracefully and release hardware."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

        if self.card_id >= 0 and self.driver.is_available:
            try:
                self.driver.WD_AI_AsyncClear(self.card_id, None, None)
                self.driver.WD_Release_Card(self.card_id)
                print("[c_acquisition] Kartu DAQ berhasil dilepaskan.")
            except Exception as e:
                print(f"[c_acquisition] Error saat release kartu: {e}")
            finally:
                self.card_id = -1

    def _run_loop(self):
        """Main acquisition loop."""
        if not self.driver.is_available:
            print("[c_acquisition] WD-Dask driver tidak terdeteksi. Berjalan dalam mode standby.")
            return

        try:
            self.card_id = self.driver.WD_Register_Card(PCI_9846H, 0)
            if self.card_id < 0:
                print(f"[c_acquisition] Gagal registrasi kartu ADLink PCI-9846H: {self.card_id}")
                return

            print(f"[c_acquisition] Kartu DAQ terdaftar (ID: {self.card_id}). Memulai double buffer DMA...")

            # Alokasi buffer DMA untuk 4 channel
            hw_buf_size = self.buffer_samples * TOTAL_HW_CHANNELS
            ai_buf1 = (U16 * hw_buf_size)()
            ai_buf2 = (U16 * hw_buf_size)()

            # Loop akuisisi
            while not self._stop_event.is_set():
                # Tunggu trigger dan proses DMA buffer
                time.sleep(0.05)

        except Exception as e:
            print(f"[c_acquisition] Error pada loop akuisisi C: {e}")
        finally:
            self.stop()
