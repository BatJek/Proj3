# main.py (упрощённый)

import dearpygui.dearpygui as dpg

from nodes.factory import create_main_interface, center_viewport
from nodes.state_manager import state_manager
import time  # ← добавлено!


if __name__ == "__main__":
    dpg.create_context()

    # Загрузка шрифта...
    try:
        with dpg.font_registry():
            font_path = "I:\\My\\LLM\\RAG\\dearpygui\\Proj3\\NotoSans-Regular.ttf"
            with dpg.font(font_path, 18) as font1:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.bind_font(font1)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки шрифта: {e}")

    # Диалоги сохранения/загрузки
    with dpg.file_dialog(directory_selector=False, show=False,
                         callback=lambda s, a: state_manager.save_state(a["file_path_name"]),
                         tag="save_state_dialog", width=700, height=400,
                         default_path=state_manager.save_dir,
                         default_filename=f"state_{int(time.time())}.json"):
        dpg.add_file_extension("JSON Files (*.json){.json}", color=(255, 255, 0, 255))

    with dpg.file_dialog(directory_selector=False, show=False,
                         callback=state_manager.load_state,
                         tag="load_state_dialog", width=700, height=400,
                         default_path=state_manager.save_dir):
        dpg.add_file_extension("JSON Files (*.json){.json}", color=(255, 255, 0, 255))

    # Viewport и интерфейс
    dpg.create_viewport(title='Node Editor with Palette', resizable=True)
    dpg.setup_dearpygui()
    create_main_interface()
    center_viewport()

    dpg.show_viewport()

    # Main render loop with improved performance
    frame_count = 0
    last_time = time.time()
    
    while dpg.is_dearpygui_running():
        current_time = time.time()
        
        # Check for autosave every 60 seconds
        if getattr(state_manager, 'autosave_enabled', False):
            last_save = getattr(state_manager, 'last_autosave', 0)
            if current_time - last_save > 60:
                state_manager.save_state(f"{state_manager.save_dir}/autosave_{int(current_time)}.json")
                state_manager.last_autosave = current_time
        
        # Optimize rendering by limiting frame rate to 60 FPS
        if current_time - last_time >= 1/60:
            dpg.render_dearpygui_frame()
            last_time = current_time
            frame_count += 1

    state_manager.save_state(f"{state_manager.save_dir}/autosave_exit.json")
    dpg.destroy_context()
