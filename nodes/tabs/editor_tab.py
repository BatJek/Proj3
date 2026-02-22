# nodes/tabs/editor_tab.py

import dearpygui.dearpygui as dpg
from nodes.registry import NODE_REGISTRY, init_themes

class EditorTab:
    def create(self, parent_window):
        with dpg.tab(label="  Tab editor  ", parent=parent_window):
            with dpg.group(horizontal=True):
                # Палитра
                with dpg.child_window(
                    tag="Node_Palette_Box",
                    width=180,
                    height=600,
                    border=True,
                    no_scrollbar=False
                ):
                    dpg.add_input_text(tag="search_input", hint="Search...", width=-1)
                    dpg.add_separator()
                    dpg.add_child_window(tag="palette_container", width=-1, height=-1)

                # Редактор
                with dpg.child_window(
                    tag="Node_Editor_Box",
                    width=-1,
                    height=600,
                    border=True,
                    drop_callback=None,  # ← будет задано в factory.py
                    payload_type="NODE"
                ):
                    self.node_editor = dpg.add_node_editor(
                        tag="node_editor",
                        width=-1,
                        height=-1,
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                        callback=None,  # ← будет задано в factory.py
                        delink_callback=None  # ← будет задано в factory.py
                    )
                    
        init_themes()