"""Persistent user settings (pure Python, no Dear PyGui).

Settings are a flat dict with dotted keys ("view.ppi", "fft.y_min", ...). The
UI layer (app/ui_shell.py) owns *applying* a value to the widgets; this module
only stores, validates against DEFAULTS, and reads/writes settings.json.
"""

import json
import os
from copy import deepcopy
from typing import Any, Dict

from config import PROJECT_ROOT

SETTINGS_FILE = str(PROJECT_ROOT / "settings.json")

DEFAULTS: Dict[str, Any] = {
    # Panels visible in the workspace (View menu)
    "view.ppi": True,
    "view.fft": True,
    "view.scope": True,
    "view.metrics": True,
    "view.logo": True,
    # PPI display
    "ppi.rings": True,
    "ppi.ring_labels": True,
    "ppi.spokes": True,
    "ppi.history": 50,
    # Spectrum defaults
    "fft.span_khz": 10000.0,
    "fft.y_lock": True,
    "fft.y_min": -110.0,
    "fft.y_max": 10.0,
    # Oscilloscope defaults (labels from app.callbacks TIME_DIV_OPTIONS / V_DIV_OPTIONS)
    "scope.time_div": "100 us/div (1 ms)",
    "scope.v_div": "250 mV/div (+/-1.0V)",
    "scope.y_lock": True,
}

_current: Dict[str, Any] = deepcopy(DEFAULTS)


def get(key: str) -> Any:
    return _current.get(key, DEFAULTS.get(key))


def set(key: str, value: Any) -> None:  # noqa: A001 - module-level API, mirrors get()
    if key not in DEFAULTS:
        raise KeyError(f"Unknown setting: {key}")
    _current[key] = value


def snapshot() -> Dict[str, Any]:
    return deepcopy(_current)


def restore(values: Dict[str, Any]) -> None:
    _current.clear()
    _current.update(_merge_with_defaults(values))


def reset_to_defaults() -> None:
    restore(DEFAULTS)


def _merge_with_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only known keys whose type matches the default; fall back to defaults otherwise."""
    merged = deepcopy(DEFAULTS)
    for key, default in DEFAULTS.items():
        if key not in data:
            continue
        value = data[key]
        if isinstance(default, bool):
            if isinstance(value, bool):
                merged[key] = value
        elif isinstance(default, (int, float)):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                merged[key] = type(default)(value)
        elif isinstance(value, type(default)):
            merged[key] = value
    return merged


def load(path: str = SETTINGS_FILE) -> Dict[str, Any]:
    """Load settings from disk (missing/corrupt file -> defaults)."""
    data: Dict[str, Any] = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                data = raw
        except Exception as e:
            print(f"[settings] Failed to read {path}, using defaults: {e}")
    restore(data)
    return snapshot()


def save(path: str = SETTINGS_FILE) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_current, f, indent=2)
        return True
    except Exception as e:
        print(f"[settings] Failed to write {path}: {e}")
        return False
