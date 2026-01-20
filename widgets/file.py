# widgets/file.py
import dearpygui.dearpygui as dpg
import os

LOG_DIR = "log"

def refresh_log_files():
    """Mencari file di direktori log dan memperbarui listbox."""
    if not os.path.exists(LOG_DIR):
        dpg.configure_item("log_file_list", items=["Log directory not found."])
        return
    
    try:
        files = [f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))]
        if not files:
            dpg.configure_item("log_file_list", items=["No log files found."])
        else:
            # Sort files by modification time (newest first)
            files_with_time = []
            for f in files:
                file_path = os.path.join(LOG_DIR, f)
                mtime = os.path.getmtime(file_path)
                files_with_time.append((f, mtime))
            
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            sorted_files = [f[0] for f in files_with_time]
            dpg.configure_item("log_file_list", items=sorted_files)
    except Exception as e:
        dpg.configure_item("log_file_list", items=[f"Error: {e}"])

def create_file_explorer_widget(parent, width, height):
    """Membuat widget untuk menampilkan file log dari direktori 'log'."""
    with dpg.group(parent=parent):
        dpg.add_text("Log File Explorer")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Refresh", callback=refresh_log_files)
        
        dpg.add_listbox([], tag="log_file_list", num_items=8)
        
        # Panggil sekali saat pembuatan untuk mengisi daftar awal
        refresh_log_files()