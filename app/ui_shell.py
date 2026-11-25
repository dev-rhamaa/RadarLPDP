"""Application shell: menu bar, live status, motor control, Settings and About dialogs.

Rule of the UI: panels are display-only. Every control lives here:
  * quick actions & toggles  -> menu bar (File / View / Radar / Spectrum / Scope / Help)
  * detailed, persistent options -> Settings dialog (File > Settings..., Ctrl+,)
  * motor Start/Stop          -> always-visible button at the right of the menu bar (Space)

Menu toggles are saved immediately. The Settings dialog previews changes live;
Save writes settings.json, Cancel restores what was there when it opened.
"""

import time
from typing import Any, Dict, Optional

import dearpygui.dearpygui as dpg

from app import callbacks, settings
from app.fonts import FONT_BOLD, FONT_MONO, bind_last_item_font
from app.servo_controller import (
    get_servo_state,
    is_servo_running,
    set_servo_mode,
    set_servo_running,
    set_servo_target_degrees,
)
from config import (
    RADAR_SWEEP_ANGLE_MAX,
    RADAR_SWEEP_ANGLE_MIN,
    THEME_COLORS,
)
from widgets import PPI

C = THEME_COLORS

VIEW_PANELS = [
    ("view.ppi", "PPI Radar", "ppi_window"),
    ("view.fft", "Spectrum", "fft_window"),
    ("view.scope", "Oscilloscope", "sinewave_window"),
    ("view.metrics", "Targets", "metrics_window"),
    ("view.logo", "Logo strip", "logo_window"),
]
PPI_TOGGLES = [
    ("ppi.rings", "Range rings"),
    ("ppi.ring_labels", "Range & angle labels"),
    ("ppi.spokes", "Azimuth spokes"),
]
SPAN_OPTIONS = [
    ("10 MHz (Nyquist)", 10000.0),
    ("5 MHz  ·  15 km", 5000.0),
    ("2 MHz  ·  6 km", 2000.0),
    ("1 MHz  ·  3 km", 1000.0),
    ("500 kHz  ·  1.5 km", 500.0),
]
PRESET_ANGLES = [30.0, 60.0, 90.0, 120.0, 150.0]
SETTINGS_PAGES = ["View", "Radar / PPI", "Spectrum", "Oscilloscope"]

_settings_snapshot: Optional[Dict[str, Any]] = None
_toast_until: float = 0.0
_last_status_poll: float = 0.0


# --------------------------------------------------------------------------- apply

def apply_setting(key: str) -> None:
    """Push one setting's current value to the UI."""
    value = settings.get(key)
    if key.startswith("view."):
        for k, _, window in VIEW_PANELS:
            if k == key and dpg.does_item_exist(window):
                dpg.configure_item(window, show=bool(value))
        callbacks.resize_callback()
    elif key == "ppi.rings":
        PPI.set_rings_visible(bool(value))
    elif key == "ppi.ring_labels":
        PPI.set_ring_labels_visible(bool(value))
    elif key == "ppi.spokes":
        PPI.set_spokes_visible(bool(value))
    elif key == "ppi.history":
        callbacks.set_target_history_size(int(value))
    elif key in ("fft.span_khz", "fft.y_min", "fft.y_max"):
        callbacks.reset_fft_view()
        _sync_span_checks(float(settings.get("fft.span_khz")))
    elif key == "fft.y_lock":
        callbacks.set_fft_y_lock(bool(value))
    elif key in ("scope.time_div", "scope.v_div"):
        callbacks.reset_scope_view()
    elif key == "scope.y_lock":
        callbacks.set_scope_y_lock(bool(value))

    # Keep any menu check item bound to this key in sync
    menu_tag = _menu_tag(key)
    if dpg.does_item_exist(menu_tag) and isinstance(value, bool):
        dpg.set_value(menu_tag, value)


def apply_all_settings() -> None:
    for key in settings.DEFAULTS:
        apply_setting(key)


def _menu_tag(key: str) -> str:
    return "menu_" + key.replace(".", "_")


def _on_menu_toggle(sender, app_data, user_data) -> None:
    """Menu check items: apply and persist right away."""
    settings.set(user_data, bool(app_data))
    apply_setting(user_data)
    settings.save()


def _menu_check(label: str, key: str) -> None:
    dpg.add_menu_item(label=label, check=True, default_value=bool(settings.get(key)),
                      tag=_menu_tag(key), callback=_on_menu_toggle, user_data=key)


# --------------------------------------------------------------------------- motor

def _current_mode() -> str:
    return get_servo_state().get("mode", "scan")


def toggle_motor(*_args) -> None:
    if is_servo_running():
        set_servo_running(False)
        if dpg.does_item_exist("menu_target_slider"):
            dpg.set_value("menu_target_slider", 90.0)
    else:
        mode = _current_mode()
        set_servo_mode(mode)
        if mode == "manual" and dpg.does_item_exist("menu_target_slider"):
            set_servo_target_degrees(float(dpg.get_value("menu_target_slider")))
        set_servo_running(True)
    refresh_motor_status()


def set_mode(mode: str) -> None:
    set_servo_mode(mode)
    refresh_motor_status()


def set_target(deg: float) -> None:
    set_servo_target_degrees(float(deg))  # also switches the servo to manual mode
    if dpg.does_item_exist("menu_target_slider"):
        dpg.set_value("menu_target_slider", float(deg))
    refresh_motor_status()


def refresh_motor_status() -> None:
    running = is_servo_running()
    mode = _current_mode()
    mode_label = "Auto scan" if mode == "scan" else "Manual"

    if dpg.does_item_exist("header_motor_status"):
        dpg.set_value("header_motor_status", f"● {'RUNNING' if running else 'STOPPED'}  ·  {mode_label}")
        dpg.configure_item("header_motor_status", color=C["success"] if running else C["text_muted"])
    if dpg.does_item_exist("motor_toggle_btn"):
        dpg.configure_item("motor_toggle_btn", label="  Stop  " if running else "  Start  ")
        dpg.bind_item_theme("motor_toggle_btn", "motor_btn_stop_theme" if running else "motor_btn_start_theme")
    if dpg.does_item_exist("menu_motor_toggle"):
        dpg.configure_item("menu_motor_toggle", label="Stop motor" if running else "Start motor")
    if dpg.does_item_exist("menu_mode_scan"):
        dpg.set_value("menu_mode_scan", mode == "scan")
        dpg.set_value("menu_mode_manual", mode == "manual")


def _create_shell_themes() -> None:
    def btn_theme(tag, bg, hover, text, pill=True):
        if dpg.does_item_exist(tag):
            return
        with dpg.theme(tag=tag):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, bg)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, hover)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text)
                if pill:  # compact pill that fits the menu bar height
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 2)

    a, d = C["accent"], C["danger"]
    btn_theme("motor_btn_start_theme", a, (130, 245, 228, 255), (12, 30, 28, 255))
    btn_theme("motor_btn_stop_theme", d, (252, 140, 140, 255), (40, 10, 10, 255))
    btn_theme("primary_btn_theme", C["accent_violet"], (160, 166, 248, 255), (16, 18, 40, 255), pill=False)

    if not dpg.does_item_exist("settings_nav_theme"):
        with dpg.theme(tag="settings_nav_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, C["background"])
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4)
                dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, 0.0, 0.5)


# --------------------------------------------------------------------------- menu bar

def _sync_span_checks(span_khz: Optional[float]) -> None:
    for idx, (_, value) in enumerate(SPAN_OPTIONS):
        if dpg.does_item_exist(f"menu_span_{idx}"):
            dpg.set_value(f"menu_span_{idx}", span_khz is not None and abs(value - span_khz) < 1e-6)


def _set_span(span_khz: float) -> None:
    callbacks.set_fft_span(span_khz)
    _sync_span_checks(span_khz)


def _zoom_fft(factor: float) -> None:
    callbacks.zoom_fft_step(factor)
    _sync_span_checks(None)


def _section(label: str) -> None:
    dpg.add_text(label.upper(), color=C["text_faint"])


def build_menu_bar() -> None:
    """Menu bar of the primary window (window must be created with menubar=True)."""
    _create_shell_themes()
    state = get_servo_state()

    with dpg.menu_bar(tag="main_menu_bar"):
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Settings...", shortcut="Ctrl+,", callback=open_settings)
            dpg.add_separator()
            dpg.add_menu_item(label="Exit", shortcut="Esc", callback=dpg.stop_dearpygui)

        with dpg.menu(label="View"):
            for key, label, _ in VIEW_PANELS:
                _menu_check(label, key)
            dpg.add_separator()
            dpg.add_menu_item(label="Show all panels", callback=_show_all_panels)

        with dpg.menu(label="Radar"):
            dpg.add_menu_item(label="Start motor", shortcut="Space", tag="menu_motor_toggle",
                              callback=toggle_motor)
            dpg.add_separator()
            _section("Mode")
            dpg.add_menu_item(label="Auto scan", check=True, tag="menu_mode_scan",
                              default_value=state.get("mode", "scan") == "scan",
                              callback=lambda: set_mode("scan"))
            dpg.add_menu_item(label="Manual", check=True, tag="menu_mode_manual",
                              default_value=state.get("mode", "scan") == "manual",
                              callback=lambda: set_mode("manual"))
            with dpg.menu(label="Manual target"):
                dpg.add_slider_float(min_value=RADAR_SWEEP_ANGLE_MIN, max_value=RADAR_SWEEP_ANGLE_MAX,
                                     default_value=float(state.get("target_deg", 90.0)), format="%.1f°",
                                     width=200, tag="menu_target_slider",
                                     callback=lambda s, a: set_target(a))
                dpg.add_separator()
                for deg in PRESET_ANGLES:
                    dpg.add_menu_item(label=f"{deg:.0f}°", callback=lambda s, a, u: set_target(u), user_data=deg)
            dpg.add_separator()
            _section("Display")
            for key, label in PPI_TOGGLES:
                _menu_check(label, key)
            dpg.add_separator()
            dpg.add_menu_item(label="Clear targets", callback=callbacks.clear_targets)

        with dpg.menu(label="Spectrum"):
            _section("Span")
            for idx, (label, value) in enumerate(SPAN_OPTIONS):
                dpg.add_menu_item(label=label, check=True, tag=f"menu_span_{idx}",
                                  callback=lambda s, a, u: _set_span(u), user_data=value)
            dpg.add_separator()
            dpg.add_menu_item(label="Zoom in", callback=lambda: _zoom_fft(0.5))
            dpg.add_menu_item(label="Zoom out", callback=lambda: _zoom_fft(2.0))
            dpg.add_menu_item(label="Fit dBm to signal", callback=callbacks.fit_fft_y)
            dpg.add_menu_item(label="Reset view", callback=lambda: apply_setting("fft.span_khz"))
            dpg.add_separator()
            _menu_check("Lock dBm axis", "fft.y_lock")

        with dpg.menu(label="Scope"):
            with dpg.menu(label="Time / div"):
                for idx, (label, _) in enumerate(callbacks.TIME_DIV_OPTIONS):
                    dpg.add_menu_item(label=label, check=True, tag=f"menu_tdiv_{idx}",
                                      callback=lambda s, a, u: callbacks.set_scope_time_div(u), user_data=label)
            with dpg.menu(label="Volt / div"):
                for idx, (label, _) in enumerate(callbacks.V_DIV_OPTIONS):
                    dpg.add_menu_item(label=label, check=True, tag=f"menu_vdiv_{idx}",
                                      callback=lambda s, a, u: callbacks.set_scope_v_div(u), user_data=label)
            dpg.add_separator()
            dpg.add_menu_item(label="Fit Y to signal", callback=callbacks.fit_scope_y)
            dpg.add_menu_item(label="Reset view", callback=callbacks.reset_scope_view)
            dpg.add_separator()
            _menu_check("Lock Y axis", "scope.y_lock")

        with dpg.menu(label="Help", tag="menu_help"):
            dpg.add_menu_item(label="Keyboard shortcuts & about", callback=open_about)

        # Right side: live status + motor button (spacer width is set every frame)
        dpg.add_spacer(width=0, tag="menubar_spacer")
        with dpg.group(horizontal=True, horizontal_spacing=14, tag="menubar_status"):
            dpg.add_text("", tag="menubar_toast", color=C["accent_violet"])
            dpg.add_text("", tag="header_motor_status")
            dpg.add_button(label="  Start  ", tag="motor_toggle_btn", callback=toggle_motor)
            dpg.add_text("|", color=C["text_faint"])
            dpg.add_text("AZ  90.0°", tag="header_azimuth_angle", color=C["text"])
            bind_last_item_font(FONT_MONO)
            dpg.add_text("0 FPS", tag="header_fps_count", color=C["text_muted"])
            bind_last_item_font(FONT_MONO)
            dpg.add_text("0 evt", tag="header_event_count", color=C["text_muted"])
            bind_last_item_font(FONT_MONO)
            dpg.add_text("--:--:--", tag="header_system_time", color=C["text_muted"])
            bind_last_item_font(FONT_MONO)
            dpg.add_spacer(width=2)

    refresh_motor_status()


def _show_all_panels() -> None:
    for key, _, _ in VIEW_PANELS:
        settings.set(key, True)
        apply_setting(key)
    settings.save()


def _align_menubar_status() -> None:
    """Push the status group to the right edge of the menu bar."""
    if not dpg.does_item_exist("menubar_status"):
        return
    state = dpg.get_item_state("menubar_status")
    if "rect_min" not in state or "rect_size" not in state:
        return
    status_x, status_w = state["rect_min"][0], state["rect_size"][0]
    if status_w <= 0:
        return
    # Shift the spacer by however far the status group is from its target x
    spacer_w = dpg.get_item_width("menubar_spacer") or 0
    target_x = dpg.get_viewport_client_width() - status_w - 14
    width = max(int(spacer_w + (target_x - status_x)), 8)
    if abs(width - spacer_w) > 1:
        dpg.set_item_width("menubar_spacer", width)


def show_toast(text: str, seconds: float = 2.5) -> None:
    global _toast_until
    if dpg.does_item_exist("menubar_toast"):
        dpg.set_value("menubar_toast", text)
        _toast_until = time.time() + seconds


def tick() -> None:
    """Per-frame shell upkeep: status alignment, toast expiry, motor state poll (2 Hz)."""
    global _last_status_poll
    _align_menubar_status()
    now = time.time()
    if _toast_until and now > _toast_until and dpg.does_item_exist("menubar_toast"):
        dpg.set_value("menubar_toast", "")
    if now - _last_status_poll > 0.5:
        _last_status_poll = now
        refresh_motor_status()


# --------------------------------------------------------------------------- settings dialog

def _on_setting_changed(sender, app_data, user_data) -> None:
    """Settings dialog widgets: live preview, not saved until Save."""
    key, convert = user_data
    settings.set(key, convert(app_data))
    apply_setting(key)


def _sw(key: str) -> str:
    return "set_" + key.replace(".", "_")


def _checkbox(key: str, label: str) -> None:
    dpg.add_checkbox(label=label, tag=_sw(key), default_value=bool(settings.get(key)),
                     callback=_on_setting_changed, user_data=(key, bool))


def _row_label(text: str, hint: str = "") -> None:
    dpg.add_spacer(height=4)
    dpg.add_text(text, color=C["text"])
    if hint:
        dpg.add_text(hint, color=C["text_muted"], wrap=380)


def _span_label(value: float) -> str:
    for label, v in SPAN_OPTIONS:
        if abs(v - value) < 1e-6:
            return label
    return SPAN_OPTIONS[0][0]


def _build_settings_dialog() -> None:
    with dpg.window(label="Settings", tag="settings_modal", modal=True, show=False, width=680, height=480,
                    no_resize=True, no_collapse=True, no_saved_settings=True, no_scrollbar=True,
                    on_close=_cancel_settings):
        with dpg.group(horizontal=True):
            with dpg.child_window(width=170, height=-46, border=False, tag="settings_nav"):
                dpg.add_spacer(height=4)
                for page in SETTINGS_PAGES:
                    dpg.add_selectable(label=f"  {page}", tag=f"settings_nav_{page}", height=26,
                                       callback=lambda s, a, u: _show_settings_page(u), user_data=page)
            dpg.bind_item_theme("settings_nav", "settings_nav_theme")

            with dpg.child_window(width=-1, height=-46, border=False):
                with dpg.group(tag="settings_page_View"):
                    _page_title("View", "Panels shown in the workspace. Hidden panels give their space to the rest.")
                    for key, label, _ in VIEW_PANELS:
                        _checkbox(key, label)

                with dpg.group(tag="settings_page_Radar / PPI", show=False):
                    _page_title("Radar / PPI", "How the plan position indicator is drawn.")
                    for key, label in PPI_TOGGLES:
                        _checkbox(key, label)
                    _row_label("Target trail length", "How many recent detections stay on the PPI.")
                    dpg.add_slider_int(tag=_sw("ppi.history"), min_value=5, max_value=300, width=280,
                                       default_value=int(settings.get("ppi.history")), format="%d targets",
                                       callback=_on_setting_changed, user_data=("ppi.history", int))

                with dpg.group(tag="settings_page_Spectrum", show=False):
                    _page_title("Spectrum", "Default view used at start-up and by Spectrum > Reset view.")
                    _row_label("Default span")
                    dpg.add_combo([lbl for lbl, _ in SPAN_OPTIONS], tag=_sw("fft.span_khz"), width=280,
                                  default_value=_span_label(float(settings.get("fft.span_khz"))),
                                  callback=_on_setting_changed,
                                  user_data=("fft.span_khz", lambda lbl: dict(SPAN_OPTIONS)[lbl]))
                    _row_label("Power range (dBm)")
                    dpg.add_drag_floatx(tag="set_fft_range", size=2, width=280, speed=0.5,
                                        min_value=-160.0, max_value=40.0, format="%.0f dBm",
                                        default_value=[float(settings.get("fft.y_min")),
                                                       float(settings.get("fft.y_max")), 0.0, 0.0],
                                        callback=_on_fft_range_changed)
                    dpg.add_spacer(height=4)
                    _checkbox("fft.y_lock", "Lock dBm axis (mouse wheel zooms frequency only)")

                with dpg.group(tag="settings_page_Oscilloscope", show=False):
                    _page_title("Oscilloscope", "Default view used at start-up and by Scope > Reset view.")
                    _row_label("Default time / div")
                    dpg.add_combo([lbl for lbl, _ in callbacks.TIME_DIV_OPTIONS], tag=_sw("scope.time_div"),
                                  width=280, default_value=settings.get("scope.time_div"),
                                  callback=_on_setting_changed, user_data=("scope.time_div", str))
                    _row_label("Default volt / div")
                    dpg.add_combo([lbl for lbl, _ in callbacks.V_DIV_OPTIONS], tag=_sw("scope.v_div"),
                                  width=280, default_value=settings.get("scope.v_div"),
                                  callback=_on_setting_changed, user_data=("scope.v_div", str))
                    dpg.add_spacer(height=4)
                    _checkbox("scope.y_lock", "Lock Y axis (mouse wheel zooms time only)")

        dpg.add_separator()
        # Footer: "Reset" left, Cancel/Save right (stretch column pushes them to the edge)
        with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False,
                       borders_innerV=False, borders_outerV=False, pad_outerX=False,
                       policy=dpg.mvTable_SizingStretchProp):
            dpg.add_table_column(init_width_or_weight=1.0)
            dpg.add_table_column(init_width_or_weight=0.0, width_fixed=True)
            with dpg.table_row():
                dpg.add_button(label="Reset to defaults", callback=_reset_settings_defaults)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Cancel", width=90, callback=_cancel_settings)
                    save = dpg.add_button(label="Save", width=90, callback=_save_settings)
                    dpg.bind_item_theme(save, "primary_btn_theme")


def _page_title(title: str, hint: str) -> None:
    dpg.add_text(title, color=C["text"])
    bind_last_item_font(FONT_BOLD)
    dpg.add_text(hint, color=C["text_muted"], wrap=440)
    dpg.add_spacer(height=6)


def _on_fft_range_changed(sender, app_data) -> None:
    lo, hi = float(app_data[0]), float(app_data[1])
    if hi - lo < 10.0:  # keep a usable range
        hi = lo + 10.0
    settings.set("fft.y_min", lo)
    settings.set("fft.y_max", hi)
    apply_setting("fft.y_min")


def _show_settings_page(page: str) -> None:
    for p in SETTINGS_PAGES:
        dpg.configure_item(f"settings_page_{p}", show=(p == page))
        dpg.set_value(f"settings_nav_{p}", p == page)


def _refresh_settings_widgets() -> None:
    for key in settings.DEFAULTS:
        tag = _sw(key)
        if not dpg.does_item_exist(tag):
            continue
        value = settings.get(key)
        dpg.set_value(tag, _span_label(float(value)) if key == "fft.span_khz" else value)
    dpg.set_value("set_fft_range", [float(settings.get("fft.y_min")), float(settings.get("fft.y_max")), 0.0, 0.0])


def open_settings(*_args) -> None:
    global _settings_snapshot
    if not dpg.does_item_exist("settings_modal"):
        _build_settings_dialog()
    if dpg.is_item_shown("settings_modal"):
        return
    _settings_snapshot = settings.snapshot()
    _refresh_settings_widgets()
    _show_settings_page(SETTINGS_PAGES[0])
    w, h = 680, 480
    dpg.set_item_pos("settings_modal", [max((dpg.get_viewport_client_width() - w) // 2, 0),
                                        max((dpg.get_viewport_client_height() - h) // 2, 0)])
    dpg.configure_item("settings_modal", show=True)


def _close_settings() -> None:
    global _settings_snapshot
    _settings_snapshot = None
    if dpg.does_item_exist("settings_modal"):
        dpg.configure_item("settings_modal", show=False)


def _save_settings(*_args) -> None:
    ok = settings.save()
    _close_settings()
    show_toast("Settings saved" if ok else "Could not save settings")


def _cancel_settings(*_args) -> None:
    if _settings_snapshot is not None:
        settings.restore(_settings_snapshot)
        apply_all_settings()
    _close_settings()


def _reset_settings_defaults(*_args) -> None:
    settings.reset_to_defaults()
    apply_all_settings()
    _refresh_settings_widgets()


# --------------------------------------------------------------------------- about

SHORTCUTS = [
    ("Space", "Start / stop motor"),
    ("Ctrl + ,", "Open Settings"),
    ("Esc", "Close dialog, or exit the app"),
    ("Mouse wheel", "Zoom spectrum / scope"),
    ("Double-click", "Fit plot to data"),
]

SYSTEM_INFO = [
    ("Radar", "FMCW C-band 5.6 GHz  ·  50 MHz sweep  ·  1 ms chirp"),
    ("Acquisition", "ADLink PCI-9846H  ·  20 MS/s  ·  zero-copy DMA  ·  ext-D trigger"),
    ("Servo", "KYDAS4801A  ·  sector 30-150°"),
    ("Project", "Radar FMCW LPDP RISPRO  ·  DKST ITB  ·  KIREI"),
]


def _build_about_dialog() -> None:
    with dpg.window(label="About & shortcuts", tag="about_modal", modal=True, show=False, width=560,
                    height=380, no_resize=True, no_collapse=True, no_saved_settings=True):
        dpg.add_text("FMCW Radar Console", color=C["text"])
        bind_last_item_font(FONT_BOLD)
        dpg.add_spacer(height=4)
        for title, rows in (("System", SYSTEM_INFO), ("Keyboard shortcuts", SHORTCUTS)):
            _section(title)
            with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False,
                           borders_innerV=False, borders_outerV=False,
                           policy=dpg.mvTable_SizingStretchProp):
                dpg.add_table_column(init_width_or_weight=0.3)
                dpg.add_table_column(init_width_or_weight=0.7)
                for left, right in rows:
                    with dpg.table_row():
                        dpg.add_text(left, color=C["text_muted"])
                        dpg.add_text(right)
            dpg.add_spacer(height=6)


def open_about(*_args) -> None:
    if not dpg.does_item_exist("about_modal"):
        _build_about_dialog()
    w, h = 560, 380
    dpg.set_item_pos("about_modal", [max((dpg.get_viewport_client_width() - w) // 2, 0),
                                     max((dpg.get_viewport_client_height() - h) // 2, 0)])
    dpg.configure_item("about_modal", show=True)


# --------------------------------------------------------------------------- keyboard

def _modal_open() -> bool:
    return any(dpg.does_item_exist(t) and dpg.is_item_shown(t) for t in ("settings_modal", "about_modal"))


def _on_escape(*_args) -> None:
    if dpg.does_item_exist("settings_modal") and dpg.is_item_shown("settings_modal"):
        _cancel_settings()
    elif dpg.does_item_exist("about_modal") and dpg.is_item_shown("about_modal"):
        dpg.configure_item("about_modal", show=False)
    else:
        dpg.stop_dearpygui()


def _on_space(*_args) -> None:
    if not _modal_open():
        toggle_motor()


def _on_comma(*_args) -> None:
    if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
        open_settings()


def register_shortcuts() -> None:
    with dpg.handler_registry(tag="shell_shortcuts"):
        dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=_on_escape)
        dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=_on_space)
        dpg.add_key_press_handler(key=dpg.mvKey_Comma, callback=_on_comma)


def init_shell() -> None:
    """Call after the workspace exists (settings already loaded): apply them, enable shortcuts."""
    apply_all_settings()
    register_shortcuts()
