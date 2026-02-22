# nodes/tabs/other_tab.py
import dearpygui.dearpygui as dpg


class OtherTab:
    def create(self, parent_window):
        with dpg.tab(label="  Other  ", parent=parent_window):
            dpg.add_text("Содержимое вкладки Other")
