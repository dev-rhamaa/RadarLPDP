"""Institutional affiliation and radar system metadata widget."""

import dearpygui.dearpygui as dpg


def _ensure_textures():
    if not dpg.does_item_exist("texture_registry"):
        dpg.add_texture_registry(tag="texture_registry")
    return "texture_registry"


def create_logo_widget(parent, width, height):
    """Widget Welcome & Affiliation: menampilkan logo LPDP, DKST ITB, dan KIREI."""
    _ensure_textures()
    logo_tags = ["logo_lpdp", "logo_dkst", "logo_kirei"]
    available_tags = [t for t in logo_tags if dpg.does_item_exist(t)]

    with dpg.group(parent=parent):

        # Tampilkan logo secara horizontal dan rapi
        with dpg.group(horizontal=True, horizontal_spacing=16):
            if available_tags:
                target_h = 50
                for tag in available_tags:
                    cfg = dpg.get_item_configuration(tag) or {}
                    tex_w = cfg.get("width", 128)
                    tex_h = cfg.get("height", 128)
                    if tex_h > 0:
                        scale = target_h / tex_h
                        disp_w = int(tex_w * scale)
                        disp_h = int(tex_h * scale)
                    else:
                        disp_w, disp_h = target_h, target_h

                    with dpg.group():
                        dpg.add_image(tag, width=disp_w, height=disp_h)
            else:
                dpg.add_text("Logo aset sedang dimuat...", color=(130, 145, 170))

        dpg.add_spacer(height=6)
        dpg.add_text("Radar FMCW LPDP RISPRO • Baseband DAQ 20 MS/s • ITB", color=(110, 125, 150))