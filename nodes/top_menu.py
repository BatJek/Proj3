# nodes/top_menu.py
import dearpygui.dearpygui as dpg


def new_file():
    # Логика создания нового проекта (например, очистка нодов)
    dpg.delete_item("node_editor", children_only=True)

def load_file():
    # Логика загрузки файла из диска
    pass

def save_file():
    # Логика сохранения текущего состояния
    pass
