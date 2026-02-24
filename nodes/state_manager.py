import json
import os
import time
import dearpygui.dearpygui as dpg

# === НЕОБХОДИМЫЕ ИМПОРТЫ ===
from .registry import create_node_instance, register_node, created_nodes, NODE_REGISTRY
from .base_node import BaseNode  # ← для attr_id_to_key_map
from .llm_nodes.llama_node import LLaMANode


class StateManager:
    def __init__(self):
        self.save_dir = "saved_states"
        self.current_file = None
        os.makedirs(self.save_dir, exist_ok=True)
    
    def save_state(self, filename=None):
        """Сохранить текущее состояние node editor"""
        if not filename:
            filename = f"{self.save_dir}/state_{int(time.time())}.json"

        state = {
            "viewport_size": [dpg.get_viewport_width(), dpg.get_viewport_height()],
            "nodes": [],
            "links": [],
            "window_positions": {}
        }

        # Сохраняем ноды
        for node_id, instance in created_nodes.items():
            if hasattr(instance, 'to_dict'):
                node_data = instance.to_dict()
                node_data["id"] = getattr(instance, 'node_id', node_id)
            else:
                node_data = {
                    "id": getattr(instance, 'node_id', node_id),
                    "label": instance.label,
                    "pos": dpg.get_item_pos(node_id) if hasattr(instance, 'node_id') and dpg.does_item_exist(node_id) else [100, 100],
                    "inputs": {},
                    "outputs": {}
                }

            state["nodes"].append(node_data)

        # Сохраняем связи по логическим ключам
        try:
            # Получаем связи из node editor
            link_items = []
            # Проверяем, существует ли редактор узлов
            if dpg.does_item_exist("node_editor"):
                # Вариант 1: Пробуем получить детей с параметром 1 (это должно быть connections)
                link_items = dpg.get_item_children("node_editor", 1) or []
                
                # Если не нашли через параметр 1, пробуем получить все элементы и отфильтровать
                if not link_items:
                    all_children = dpg.get_item_children("node_editor", 0) or []
                    for child in all_children:
                        if dpg.get_item_type(child) == "mvAppItemType::mvNodeLink":
                            link_items.append(child)
            
            print(f"🔍 Найдено связей: {len(link_items)}")  # ← отладка

            for link in link_items:
                if dpg.get_item_type(link) == "mvAppItemType::mvNodeLink":
                    cfg = dpg.get_item_configuration(link)
                    source_attr_id = int(cfg['attr_1'])
                    target_attr_id = int(cfg['attr_2'])

                    src_info = BaseNode.attr_id_to_key_map.get(source_attr_id)
                    tgt_info = BaseNode.attr_id_to_key_map.get(target_attr_id)

                    if src_info and tgt_info:
                        state["links"].append({
                            "source_node_id": src_info[0],
                            "source_key": src_info[2],
                            "target_node_id": tgt_info[0],
                            "target_key": tgt_info[2]
                        })
                    else:
                        print(f"⚠️ Не найдена информация о связях для атрибутов {source_attr_id} -> {target_attr_id}")
                        print(f"   attr_id_to_key_map: {dict(list(BaseNode.attr_id_to_key_map.items())[:10])}")  # первые 10 для отладки
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении связей: {e}")
            import traceback
            traceback.print_exc()

        # Сохраняем позиции окон
        for window_tag in ["Node_Palette_Box", "Node_Editor_Box", "status_log"]:
            if dpg.does_item_exist(window_tag):
                state["window_positions"][window_tag] = dpg.get_item_pos(window_tag)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            self.current_file = filename
            print(f"✅ Состояние сохранено в {filename}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения состояния: {e}")
            return False

    def load_state(self, sender, app_data):
        """Загрузить состояние из файла"""
        filename = app_data['file_path_name']
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Очищаем текущий node editor
            dpg.delete_item("node_editor", children_only=True)
            created_nodes.clear()

            # Создаём маппинг старых ID → новых
            old_to_new_node_ids = {}

            # Восстанавливаем ноды
            for node_data in state["nodes"]:
                node_type = node_data.get("label")
                if not node_type:
                    print(f"⚠️ Пропущен узел без label: {node_data}")
                    continue

                pos = node_data.get("pos", [100, 100])
                # Убедимся, что pos — это список/кортеж из двух чисел
                if isinstance(pos, list) and len(pos) == 2:
                    pass
                elif isinstance(pos, (tuple, list)) and len(pos) >= 2:
                    pos = [pos[0], pos[1]]
                else:
                    pos = [100, 100]

                node = create_node_instance(node_type, parent="node_editor", pos=pos)
                if not node:
                    print(f"⚠️ Не удалось создать узел типа '{node_type}'")
                    continue

                node_id = node.create()
                register_node(node)

                original_id = node_data.get("id")
                if original_id is not None:
                    old_to_new_node_ids[original_id] = node_id

                # Восстанавливаем состояние
                if hasattr(node, 'from_dict'):
                    node.from_dict(node_data)

            # ⚠️ КРИТИЧНО: дать DPG обработать атрибуты
            time.sleep(0.1)
            dpg.split_frame()  # ← принудительно обновляет UI и регистрирует атрибуты
            time.sleep(0.2)

            print(f"🔍 attr_id_to_key_map после создания нод = {BaseNode.attr_id_to_key_map}")

            # Восстанавливаем связи по логическим ключам
            for link_data in state.get("links", []):
                source_node_old_id = link_data.get("source_node_id")
                target_node_old_id = link_data.get("target_node_id")
                source_key = link_data.get("source_key")
                target_key = link_data.get("target_key")

                if not all([source_node_old_id, target_node_old_id, source_key, target_key]):
                    print(f"⚠️ Неполные данные связи: {link_data}")
                    continue

                new_source_id = old_to_new_node_ids.get(source_node_old_id)
                new_target_id = old_to_new_node_ids.get(target_node_old_id)

                if not (new_source_id and new_target_id):
                    print(f"⚠️ Не найдены новые ID для связи: {source_node_old_id} → {target_node_old_id}")
                    continue

                # Ищем атрибуты по node_id + key
                src_attr = next(
                    (
                        attr_id for attr_id, (nid, t, k) in BaseNode.attr_id_to_key_map.items()
                        if nid == new_source_id and t == "output" and k == source_key
                    ),
                    None
                )
                tgt_attr = next(
                    (
                        attr_id for attr_id, (nid, t, k) in BaseNode.attr_id_to_key_map.items()
                        if nid == new_target_id and t == "input" and k == target_key
                    ),
                    None
                )

                print(f"🔍 Попытка восстановить связь: {new_source_id}.{source_key} → {new_target_id}.{target_key}")
                print(f"   Найденные атрибуты: src={src_attr}, tgt={tgt_attr}")

                if not (src_attr and tgt_attr):
                    print(f"❌ Не найдены все необходимые атрибуты!")
                    continue

                # ✅ Попытка создания связи
                try:
                    link_id = dpg.add_node_link(src_attr, tgt_attr, parent="node_editor")
                    print(f"✅ Связь создана: {link_id} ({src_attr} → {tgt_attr})")
                except Exception as e:
                    print(f"❌ Ошибка при создании связи: {e}")

            # Ещё раз обновляем UI
            time.sleep(0.1)
            dpg.split_frame()

            # Восстанавливаем позиции окон
            for window_tag, pos in state.get("window_positions", {}).items():
                if dpg.does_item_exist(window_tag):
                    try:
                        dpg.set_item_pos(window_tag, pos)
                    except Exception:
                        pass

            self.current_file = filename
            print(f"✅ Состояние загружено из {filename}")
            return True

        except FileNotFoundError:
            print(f"❌ Файл не найден: {filename}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка JSON в файле {filename}: {e}")
            return False
        except Exception as e:
            import traceback
            print(f"❌ Ошибка загрузки состояния: {e}")
            traceback.print_exc()
            return False

    def _get_node_class_by_type(self, node_type):
        """Получить класс ноды по типу"""
        for category, nodes in NODE_REGISTRY.items():
            for node_name, node_config in nodes.items():
                if node_name == node_type:
                    return node_config["class"]
        return None

    def get_recent_files(self):
        """Получить список последних сохраненных файлов"""
        files = []
        for file in os.listdir(self.save_dir):
            if file.endswith('.json'):
                files.append(os.path.join(self.save_dir, file))
        return sorted(files, key=lambda x: os.path.getmtime(x), reverse=True)[:10]


# Глобальный экземпляр
state_manager = StateManager()
