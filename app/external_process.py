import os
import sys
import subprocess
import signal
from pathlib import Path
from typing import Dict, Any, Optional

# Global process handle
_proc: Optional[subprocess.Popen] = None


def _resolve_exe_path(exe_name: str, cwd: Optional[str]) -> Path:
    """Resolve the path to the executable.
    - If absolute, return as-is.
    - If relative and cwd provided, check cwd first.
    - Otherwise search in project root and current module dir.
    """
    p = Path(exe_name)
    if p.is_absolute():
        return p

    if cwd:
        candidate = Path(cwd) / exe_name
        if candidate.exists():
            return candidate

    app_dir = Path(__file__).resolve().parent  # .../app
    project_root = app_dir.parent              # project root

    for candidate in [project_root / exe_name, app_dir / exe_name]:
        if candidate.exists():
            return candidate

    # Fallback to project_root/exe_name even if doesn't exist, so error is explicit on start
    return project_root / exe_name


def _is_platform_allowed(only_on_platforms) -> bool:
    if not only_on_platforms:
        return True
    try:
        allowed = set(only_on_platforms)
    except TypeError:
        return False
    return sys.platform in allowed


from app.c_acquisition import NativeCAcquisitionEngine

# Global native acquisition engine
_native_engine: Optional[NativeCAcquisitionEngine] = None


def start_worker(cfg: Dict[str, Any]) -> Optional[int]:
    """Start acquisition engine (prefers embedded C DAQ engine if available, or falls back to subprocess)."""
    global _proc, _native_engine
    
    # Try embedded native C DAQ engine first
    if _native_engine is None:
        _native_engine = NativeCAcquisitionEngine()
    
    if _native_engine.driver.is_available:
        print("[external_worker] Menggunakan Embedded C DAQ Engine langsung di Python.")
        _native_engine.start()
        return os.getpid()

    if _proc and _proc.poll() is None:
        return _proc.pid

    if not cfg.get("enabled", False):
        return None

    if not _is_platform_allowed(cfg.get("only_on_platforms")):
        return None

    exe_name = cfg.get("exe_name")
    if not exe_name:
        raise ValueError("EXTERNAL_WORKER.exe_name is required when enabled=True")

    args = list(cfg.get("args", []))
    cwd_cfg = cfg.get("cwd")
    env_cfg = dict(cfg.get("env", {})) or None

    exe_path = _resolve_exe_path(exe_name, cwd_cfg)
    if not exe_path.exists():
        print(f"[external_worker] Warning: Executable {exe_path} tidak ditemukan. Berjalan tanpa subprocess.")
        return None

    cmd = [str(exe_path)] + args

    popen_kwargs: Dict[str, Any] = dict(
        cwd=(cwd_cfg or str(exe_path.parent)),
        env=(os.environ | env_cfg) if env_cfg else None,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Detach properly per platform
    if sys.platform == "win32":
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        popen_kwargs["creationflags"] = CREATE_NO_WINDOW | DETACHED_PROCESS
    else:
        popen_kwargs["preexec_fn"] = os.setsid

    try:
        _proc = subprocess.Popen(cmd, **popen_kwargs)
        return _proc.pid
    except Exception as e:
        print(f"[external_worker] Gagal memulai subprocess {cmd}: {e}")
        return None


def stop_worker(timeout: float = 3.0) -> None:
    """Stop the acquisition engine gracefully."""
    global _proc, _native_engine
    
    if _native_engine:
        _native_engine.stop()

    if not _proc:
        return

    if _proc.poll() is not None:
        _proc = None
        return

    try:
        if sys.platform == "win32":
            _proc.terminate()
        else:
            os.killpg(os.getpgid(_proc.pid), signal.SIGTERM)
        _proc.wait(timeout=timeout)
    except Exception:
        try:
            if sys.platform == "win32":
                _proc.kill()
            else:
                os.killpg(os.getpgid(_proc.pid), signal.SIGKILL)
        except Exception:
            pass
    finally:
        _proc = None
