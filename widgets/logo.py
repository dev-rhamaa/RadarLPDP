# UI/widgets/logo.py
import dearpygui.dearpygui as dpg

def _ensure_textures():
    if not dpg.does_item_exist("texture_registry"):
        dpg.add_texture_registry(tag="texture_registry")
    return "texture_registry"

def create_logo_widget(parent, width, height):
    """Widget Welcome: menampilkan logo LPDP, DKST ITB, dan KIREI."""
    _ensure_textures()  # make sure registry exists (created in setup and here as safety)
    # Hanya referensi tekstur yang sudah dipreload oleh app.setup._preload_textures
    logo_tags = ["logo_lpdp", "logo_dkst", "logo_kirei"]
    available_tags = [t for t in logo_tags if dpg.does_item_exist(t)]

    with dpg.group(parent=parent):
        dpg.add_spacer(height=8)
        dpg.add_spacer(height=4)
        dpg.add_separator()
        dpg.add_spacer(height=8)

        # Tampilkan logo secara horizontal dan terpusat
        with dpg.group(horizontal=True, horizontal_spacing=12):
            if available_tags:
                target_h = 64  # tinggi kecil agar rapi dan fit
                for tag in available_tags:
                    cfg = dpg.get_item_configuration(tag) or {}
                    tex_w = cfg.get("width", 128)
                    tex_h = cfg.get("height", 128)
                    # Skala menjaga rasio aspek
                    if tex_h > 0:
                        scale = target_h / tex_h
                        disp_w = int(tex_w * scale)
                        disp_h = int(tex_h * scale)
                    else:
                        disp_w, disp_h = target_h, target_h
                    # Bungkus setiap logo dalam group kecil agar mudah dipusatkan/ditata
                    with dpg.group():
                        dpg.add_spacer(width=4)
                        dpg.add_image(tag, width=disp_w, height=disp_h)
                        dpg.add_spacer(width=4)
            else:
                dpg.add_text("Logo belum dimuat. Pastikan file Assets tersedia.")

        dpg.add_spacer(height=8)
        dpg.add_separator()