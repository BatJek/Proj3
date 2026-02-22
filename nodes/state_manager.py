import json
import os
import time
import dearpygui.dearpygui as dpg
from .registry import get_node_instance, NODE_REGISTRY, created_nodes
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
                # Добавляем ID ноды в данные
                node_data["id"] = getattr(instance, 'node_id', node_id)
            else:
                # Альтернативный способ сохранения состояния для нод без to_dict
                node_data = {
                    "id": getattr(instance, 'node_id', node_id),
                    "label": getattr(instance, '__class__', type(instance)).__name__,
                    "pos": dpg.get_item_pos(instance.node_id) if hasattr(instance, 'node_id') and dpg.does_item_exist(instance.node_id) else [100, 100],
                    "inputs": {},
                    "outputs": {}
                }
                
                # Сохраняем значения входов
                if hasattr(instance, 'inputs'):
                    for input_name, input_item in instance.inputs.items():
                        try:
                            value = dpg.get_value(input_item)
                            if value is not None:
                                node_data["inputs"][input_name] = value
                        except:
                            pass
                
                # Сохраняем значения выходов
                if hasattr(instance, 'outputs'):
                    for output_name, output_item in instance.outputs.items():
                        try:
                            value = dpg.get_value(output_item)
                            if value is not None:
                                node_data["outputs"][output_name] = value
                        except:
                            pass
            
            state["nodes"].append(node_data)
        
        # Сохраняем связи
        try:
            links = dpg.get_item_children("node_editor", 1)  # Получаем связи из node editor
            if links:
                for link in links:
                    if dpg.get_item_type(link) == "mvAppItemType::mvNodeLink":
                        source_attr = dpg.get_item_configuration(link)['attr_1']  # Источник
                        target_attr = dpg.get_item_configuration(link)['attr_2']  # Цель
                        
                        # Получаем информацию о том, к каким узлам принадлежат атрибуты
                        source_node_id = dpg.get_item_parent(source_attr)
                        target_node_id = dpg.get_item_parent(target_attr)
                        
                        # Также получаем ключи атрибутов для правильного восстановления
                        from .base_node import BaseNode
                        source_key_info = BaseNode.attr_id_to_key_map.get(int(source_attr), (None, None, None))
                        target_key_info = BaseNode.attr_id_to_key_map.get(int(target_attr), (None, None, None))
                        
                        state["links"].append({
                            "source": int(source_attr),
                            "target": int(target_attr),
                            "source_node": int(source_node_id),
                            "target_node": int(target_node_id),
                            "source_key": source_key_info[2],  # Ключ атрибута источника
                            "target_key": target_key_info[2]   # Ключ атрибута цели
                        })
        except Exception as e:
            print(f"⚠️ Не удалось получить связи: {e}")
        
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
            
            # Очищаем глобальный реестр нод
            created_nodes.clear()
            
            # Создаем маппинг между старыми и новыми ID нод для правильного восстановления связей
            old_to_new_node_ids = {}
            
            # Восстанавливаем ноды
            for node_data in state["nodes"]:
                node_type = node_data.get("label", "Unknown")
                pos = node_data.get("pos", [100, 100])
                
                # Создаем ноду через фабрику
                from .registry import create_node_instance, register_node
                node = create_node_instance(node_type, parent="node_editor", pos=pos)
                
                if node:
                    node_id = node.create()
                    
                    # Регистрируем ноду в глобальном реестре
                    register_node(node)
                    
                    # Сохраняем соответствие старого ID новому
                    original_id = node_data.get("id", node_id)
                    old_to_new_node_ids[original_id] = node_id
                    
                    # Восстанавливаем внутреннее состояние ноды
                    if hasattr(node, 'from_dict'):
                        node.from_dict(node_data)
                    else:
                        # Альтернативное восстановление состояния для нод без from_dict
                        for key, value in node_data.get("inputs", {}).items():
                            if hasattr(node, 'inputs') and key in node.inputs:
                                try:
                                    dpg.set_value(node.inputs[key], value)
                                except:
                                    pass
                        for key, value in node_data.get("outputs", {}).items():
                            if hasattr(node, 'outputs') and key in node.outputs:
                                try:
                                    dpg.set_value(node.outputs[key], value)
                                except:
                                    pass
            
            # Обновляем время после создания всех нод
            import time
            time.sleep(0.1)  # Небольшая задержка для обновления GUI
            
            # Восстанавливаем связи
            for link_data in state.get("links", []):  # Используем .get() на случай отсутствия ключа
                source_attr = link_data["source"]
                target_attr = link_data["target"]
                
                # Проверяем существование атрибутов перед созданием связи
                if dpg.does_item_exist(source_attr) and dpg.does_item_exist(target_attr):
                    try:
                        dpg.add_node_link(source_attr, target_attr, parent="node_editor")
                    except Exception as e:
                        print(f"⚠️ Не удалось создать связь: {e}")
                else:
                    # Если атрибуты не существуют, пытаемся найти подходящие атрибуты по информации из сохраненного состояния
                    try:
                        source_key = link_data.get("source_key")
                        target_key = link_data.get("target_key")
                        source_node_old_id = link_data.get("source_node")
                        target_node_old_id = link_data.get("target_node")
                        
                        if source_key and target_key:
                            # Нужно найти новые ID атрибутов по старым ID узлов и ключам
                            # Для этого нужно установить связи между новыми узлами, основываясь на сохраненной информации
                            # Это требует более сложной логики, так как мы должны сопоставить старые и новые ID
                            
                            # Находим новые ID узлов по соответствию
                            new_source_node_id = old_to_new_node_ids.get(source_node_old_id)
                            new_target_node_id = old_to_new_node_ids.get(target_node_old_id)
                            
                            if new_source_node_id and new_target_node_id:
                                # Теперь нужно найти атрибуты в новых узлах по ключам
                                # Это требует дополнительной информации о структуре узлов
                                
                                # Пока используем простой способ - поиск по меткам атрибутов
                                # Получаем дочерние элементы каждого узла (это будут атрибуты)
                                source_attrs = dpg.get_item_children(new_source_node_id, 1) or []
                                target_attrs = dpg.get_item_children(new_target_node_id, 1) or []
                                
                                # Находим нужные атрибуты по ключам (метке)
                                matched_source_attr = None
                                matched_target_attr = None
                                
                                for attr_id in source_attrs:
                                    if dpg.has_item_component(attr_id, dpg.mvNodeAttr_Output):
                                        # Это выходной атрибут, проверим его метку
                                        config = dpg.get_item_configuration(attr_id)
                                        # Для поиска по ключу нам нужно знать, как он хранится в интерфейсе
                                        # Поскольку мы не можем напрямую получить ключ, будем использовать другую стратегию
                                        
                                        # Используем глобальную карту атрибутов для поиска
                                        from .base_node import BaseNode
                                        for attr_id_check, (node_id, attr_type, key) in BaseNode.attr_id_to_key_map.items():
                                            if node_id == new_source_node_id and attr_type == "output" and key == source_key:
                                                matched_source_attr = attr_id_check
                                                break
                                
                                for attr_id in target_attrs:
                                    if dpg.has_item_component(attr_id, dpg.mvNodeAttr_Input):
                                        # Это входной атрибут, проверим его метку
                                        config = dpg.get_item_configuration(attr_id)
                                        
                                        # Используем глобальную карту атрибутов для поиска
                                        from .base_node import BaseNode
                                        for attr_id_check, (node_id, attr_type, key) in BaseNode.attr_id_to_key_map.items():
                                            if node_id == new_target_node_id and attr_type == "input" and key == target_key:
                                                matched_target_attr = attr_id_check
                                                break
                                
                                if matched_source_attr and matched_target_attr:
                                    try:
                                        dpg.add_node_link(matched_source_attr, matched_target_attr, parent="node_editor")
                                    except Exception as e:
                                        print(f"⚠️ Не удалось создать связь по ключам: {e}")
                                else:
                                    print(f"⚠️ Не удалось найти атрибуты для связи: {source_key} -> {target_key}")
                    except Exception as e:
                        print(f"⚠️ Ошибка при восстановлении связи по ключам: {e}")
            
            # Восстанавливаем позиции окон
            for window_tag, pos in state.get("window_positions", {}).items():
                if dpg.does_item_exist(window_tag):
                    dpg.set_item_pos(window_tag, pos)
            
            self.current_file = filename
            print(f"✅ Состояние загружено из {filename}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Файл не найден: {filename}")
            return False
        except json.JSONDecodeError:
            print(f"❌ Ошибка чтения JSON из файла: {filename}")
            return False
        except Exception as e:
            print(f"❌ Ошибка загрузки состояния: {e}")
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