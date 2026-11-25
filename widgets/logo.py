"""Institutional affiliation strip (DKST ITB, KIREI). Toggle via View > Logo."""

import dearpygui.dearpygui as dpg

from config import THEME_COLORS

LOGO_HEIGHT = 40


def create_logo_widget(parent, width, height):
    available = [t for t in ("logo_dkst", "logo_kirei") if dpg.does_item_exist(t)]
    with dpg.group(parent=parent, horizontal=True, horizontal_spacing=20):
        for tag in available:
            cfg = dpg.get_item_configuration(tag) or {}
            tex_w, tex_h = cfg.get("width", 128), cfg.get("height", 128)
            scale = LOGO_HEIGHT / tex_h if tex_h else 1.0
            dpg.add_image(tag, width=int(tex_w * scale), height=int(tex_h * scale))
        if not available:
            dpg.add_text("Radar FMCW LPDP RISPRO  ·  ITB", color=THEME_COLORS["text_muted"])
