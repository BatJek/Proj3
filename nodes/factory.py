# nodes/factory.py (обновлённая версия)

import dearpygui.dearpygui as dpg
import tkinter as tk
from tkinter import filedialog

from nodes.tabs import EditorTab, LLMTab, OtherTab
from nodes.registry import create_node_instance, NODE_REGISTRY, change_theme
from nodes.execution_manager import execution_manager
from nodes.state_manager import state_manager


# === Вспомогательные функции ===

def get_screen_size():
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()
    return screen_width, screen_height


def center_viewport():
    screen_width, screen_height = get_screen_size()
    viewport_width = int(screen_width * 0.75)
    viewport_height = int(screen_height * 0.75)

    dpg.set_viewport_width(viewport_width)
    dpg.set_viewport_height(viewport_height)

    x = (screen_width - viewport_width) // 2
    y = (screen_height - viewport_height) // 2
    dpg.set_viewport_pos([x, y])
    print(f"✅ Viewport: {viewport_width}x{viewport_height} @ [{x}, {y}]")


# === Глобальное состояние ===

node_editor_running = False


def toggle_run_callback(sender, app_data, user_data):
    global node_editor_running
    node_editor_running = not node_editor_running

    if node_editor_running:
        dpg.configure_item("run_button", label="Stop")
        change_theme()
        execution_manager.start_execution()
        dpg.configure_item("status_text", label="Nodes are running")
    else:
        dpg.configure_item("run_button", label="Run")
        execution_manager.stop_execution()
        dpg.configure_item("status_text", label="Stopped")


# === Связи и удаление нод ===

active_links = []


def on_link_created(sender, app_data, user_data):
    source_attr_tag, target_attr_tag = app_data
    link_id = dpg.add_node_link(source_attr_tag, target_attr_tag, parent=sender)
    active_links.append((source_attr_tag, target_attr_tag, link_id))
    print(f"🔗 Соединение создано: {source_attr_tag} -> {target_attr_tag}")

    current_links_only_attrs = [(src, tgt) for src, tgt, _ in active_links]
    execution_manager.update_links(current_links_only_attrs)


def on_link_deleted(sender, app_data, user_data):
    source_attr_tag, target_attr_tag = app_data
    link_to_remove = None

    for src, tgt, link_id in active_links:
        if src == source_attr_tag and tgt == target_attr_tag:
            link_to_remove = link_id
            break

    if link_to_remove:
        dpg.delete_item(link_to_remove)
        active_links.remove((source_attr_tag, target_attr_tag, link_to_remove))
        print(f"❌ Удалено соединение: {source_attr_tag} -> {target_attr_tag}")

        current_links_only_attrs = [(src, tgt) for src, tgt, _ in active_links]
        execution_manager.update_links(current_links_only_attrs)


# === Удаление нод по Delete ===

def on_delete_key():
    selected_nodes = dpg.get_selected_nodes("node_editor")
    if not selected_nodes:
        return

    nodes_to_delete = list(selected_nodes)

    for node_id in nodes_to_delete:
        _delete_node_links(node_id)
        from nodes.registry import created_nodes, unregister_node
        node_instance = created_nodes.get(node_id)

        if dpg.does_item_exist(node_id):
            dpg.delete_item(node_id)

        execution_manager.unregister_node(node_id)
        if node_id in created_nodes:
            unregister_node(node_id)

        _cleanup_node_attributes(node_id)

    current_links_only_attrs = [(src, tgt) for src, tgt, _ in active_links]
    execution_manager.update_links(current_links_only_attrs)


def _delete_node_links(node_id):
    links_to_remove = []
    for src, tgt, link_id in active_links:
        try:
            src_parent = dpg.get_item_parent(src)
            tgt_parent = dpg.get_item_parent(tgt)

            if src_parent == node_id or tgt_parent == node_id:
                links_to_remove.append((src, tgt, link_id))
        except Exception:
            continue

    for src, tgt, link_id in links_to_remove:
        if dpg.does_item_exist(link_id):
            dpg.delete_item(link_id)
        if (src, tgt, link_id) in active_links:
            active_links.remove((src, tgt, link_id))


def _cleanup_node_attributes(node_id):
    from nodes.base_node import BaseNode
    attrs_to_remove = [
        attr_id for attr_id, (nid, _, _) in BaseNode.attr_id_to_key_map.items()
        if nid == node_id
    ]
    for attr_id in attrs_to_remove:
        del BaseNode.attr_id_to_key_map[attr_id]


# === Drag & Drop ===

# nodes/factory.py — исправленный _drop_callback

def _drop_callback(sender, app_data, user_data):
    if not app_data:
        print("No app_data received")
        return

    try:
        mouse_global = dpg.get_mouse_pos(local=False)

        # Получаем координаты левого верхнего угла node_editor (включая рамку)
        editor_rect_min = dpg.get_item_rect_min("node_editor")
        if not editor_rect_min:
            print("⚠️ Could not get rect min of 'node_editor'")
            return

        # Вычисляем координаты внутри редактора
        adjusted_x = mouse_global[0] - editor_rect_min[0]
        adjusted_y = mouse_global[1] - editor_rect_min[1]
        
        print(f"Mouse global: {mouse_global}")
        print(f"node_editor rect min: {editor_rect_min}")
        print(f"Adjusted pos: ({adjusted_x:.1f}, {adjusted_y:.1f})")


    except Exception as e:
        print(f"⚠️ Fallback to default position due to error: {e}")
        screen_w = dpg.get_viewport_width()
        screen_h = dpg.get_viewport_height()
        adjusted_x = screen_w * 0.3
        adjusted_y = screen_h * 0.4

    try:
        instance = create_node_instance(app_data, parent="node_editor", pos=(adjusted_x-470, adjusted_y-150))
        if not instance:
            print("❌ Failed to create node instance")
            return

        node_id = instance.create()
        if not node_id:
            print("❌ Failed to create node UI")
            return

        from nodes.registry import register_node
        register_node(instance)
        execution_manager.register_node(instance, node_id)

        print(f"✅ Node created at ({adjusted_x:.1f}, {adjusted_y:.1f}): {instance.label} (ID: {node_id})")

    except Exception as e:
        print(f"ERROR in drop_callback: {str(e)}")
        import traceback
        traceback.print_exc()
        # Убедимся, что все ошибки обрабатываются корректно





# === Палитра нод ===

def _update_palette():
    query = dpg.get_value("search_input").lower().strip()
    dpg.delete_item("palette_container", children_only=True)

    for category, nodes in NODE_REGISTRY.items():
        matching_nodes = [n for n in nodes if query in n.lower()]
        if query and not matching_nodes:
            continue

        with dpg.tree_node(label=f" {category}", default_open=True, parent="palette_container") as tree_node_id:
            for node_name in (matching_nodes if query else nodes):
                btn = dpg.add_button(
                    label=f"➕ {node_name}",
                    width=-1,
                    parent=tree_node_id
                )
                with dpg.drag_payload(parent=btn, drag_data=node_name, payload_type="NODE"):
                    dpg.add_text(f"Create {node_name} node")

                node_info = nodes[node_name]
                description = node_info.get("description", f"Description for {node_name} not available.")

                with dpg.theme() as tooltip_theme:
                    with dpg.theme_component(dpg.mvAll):
                        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (50, 50, 50, 255))
                        dpg.add_theme_color(dpg.mvThemeCol_Text, (150, 0, 0, 255))
                        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 5, 5)

                with dpg.tooltip(parent=btn):
                    dpg.add_text(description)
                    dpg.bind_item_theme(dpg.last_item(), tooltip_theme)

        dpg.add_spacing(count=2, parent="palette_container")


def on_search_change(sender, app_data, user_data):
    _update_palette()


# === Ресайз окна ===

def on_resize():
    viewport_w = dpg.get_viewport_width()
    viewport_h = dpg.get_viewport_height()

    palette_width = int(viewport_w * 0.2)
    editor_width = viewport_w - palette_width
    editor_palette_h = int(viewport_h * 0.75)
    log_h = viewport_h - editor_palette_h

    dpg.set_item_width("Node_Palette_Box", palette_width)
    dpg.set_item_width("Node_Editor_Box", editor_width)

    dpg.set_item_width("main_window", viewport_w)
    dpg.set_item_height("main_window", viewport_h)

    dpg.set_item_width("status_log", viewport_w)
    dpg.set_item_height("Node_Palette_Box", editor_palette_h - 40)
    dpg.set_item_height("Node_Editor_Box", editor_palette_h - 40)
    dpg.set_item_height("status_log", max(100, log_h))

    dpg.set_item_pos("main_window", [0, 0])


# === Создание интерфейса ===

def create_main_interface():
    with dpg.window(
        tag="main_window",
        no_title_bar=True,
        no_resize=True,
        no_move=True,
        no_scrollbar=True,
        no_collapse=True,
        no_background=False
    ):
        # Меню
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Новый", callback=lambda: dpg.delete_item("node_editor", children_only=True), tag="new_file_item")
                dpg.add_menu_item(label="Загрузить", callback=state_manager.load_state, tag="load_file_item")
                dpg.add_menu_item(label="Сохранить", callback=state_manager.save_state, tag="save_file_item")
                dpg.add_separator()
                dpg.add_menu_item(label="Сохранить состояние",
                                  callback=lambda: dpg.show_item("save_state_dialog"))
                dpg.add_menu_item(label="Загрузить состояние",
                                  callback=lambda: dpg.show_item("load_state_dialog"))
                dpg.add_menu_item(label="Автосохранение",
                                  callback=lambda s, a: setattr(state_manager, 'autosave_enabled', a),
                                  check=True)
            dpg.add_button(label="Run", tag="run_button", callback=toggle_run_callback)

        # Вкладки
        with dpg.tab_bar() as tab_bar:
            EditorTab().create(tab_bar)
            LLMTab().create(tab_bar)
            OtherTab().create(tab_bar)

        # Лог статуса
        with dpg.child_window(
            tag="status_log",
            width=-1,
            height=200,
            label="Execution Status",
            no_scrollbar=False
        ):
            dpg.add_text("Status: Stopped", tag="status_text")

    # 🔁 Привязываем callback'и ПОСЛЕ создания интерфейса (чтобы избежать цикла)
    _bind_callbacks()

    dpg.set_viewport_resize_callback(lambda: on_resize())
    dpg.set_item_pos("main_window", [0, 0])
    on_resize()
    _update_palette()


def _bind_callbacks():
    """Привязывает callback'и после создания UI"""
    # Привязываем drop_callback
    dpg.configure_item(
        "Node_Editor_Box",
        drop_callback=_drop_callback,
        payload_type="NODE"
    )

    # Привязываем callback'и node_editor
    dpg.configure_item(
        "node_editor",
        callback=on_link_created,
        delink_callback=on_link_deleted
    )

    # Регистрируем обработчик Delete
    with dpg.handler_registry():
        dpg.add_key_press_handler(dpg.mvKey_Delete, callback=on_delete_key)


# === Экспорт ===

__all__ = [
    "create_main_interface",
    "center_viewport",
    "toggle_run_callback"
]
