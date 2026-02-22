# nodes/base_node.py

import dearpygui.dearpygui as dpg
from abc import ABC, abstractmethod

class BaseNode(ABC):
    # Добавим классовые атрибуты для хранения соответствия ID <-> Key
    # Это будет использоваться ExecutionManager
    attr_id_to_key_map = {} # {attr_id: (node_id, "input"/"output", key)}

    
    def __init__(self, label: str, parent="node_editor", pos=None):
        self.label = label
        self.parent = parent
        self.pos = pos or (0, 0)
        self.node_id = None
        self.outputs = {}
        self.inputs = {}
        # --- НОВОЕ: внутреннее состояние для данных ---
        self.state = {"inputs": {}, "outputs": {}}
        # ---
        self.outputs = {}
        self.inputs = {}


    
    def create(self):
        """Создает ноду в Dear PyGui"""
        
        # Убедитесь, что родитель существует перед созданием узла
        if not dpg.does_item_exist(self.parent):
            print(f"Parent {self.parent} does not exist!")
            return None

        try:
            with dpg.node(label=self.label, parent=self.parent, pos=self.pos) as self.node_id:
                # Создаем атрибуты узла
                self._create_inputs()
                self._create_outputs()


            # === ОГРАНИЧЕНИЕ ШИРИНЫ ПОСЛЕ СОЗДАНИЯ ===
            if hasattr(self, 'max_node_width'):
                dpg.set_item_width(self.node_id, self.max_node_width)
                print(f"✅ Установлена ширина ноды {self.label}: {self.max_node_width}px")
                    # Если есть дополнительные элементы - добавляем их здесь

        except Exception as e:
            print(f"Error creating node: {e}")
            import traceback
            traceback.print_exc()
            return None

        return self.node_id
    
    @abstractmethod
    def _create_inputs(self):
        """Создает входные атрибуты"""
        pass
    
    @abstractmethod
    def _create_outputs(self):
        """Создает выходные атрибуты"""
        pass
    
    @abstractmethod
    def process(self):
        """Обрабатывает данные ноды"""
        pass

    # --- НОВЫЕ МЕТОДЫ ДЛЯ УПРАВЛЕНИЯ ДАННЫМИ ---
    def get_input_value(self, key):
        """Получает значение из внутреннего состояния или из Dear PyGui."""
        # 1. Сначала пробуем внутреннее состояние (для передачи данных от других нод)
        if key in self.state["inputs"]:
            val = self.state["inputs"][key]
            print(f"BaseNode: Got input '{key}' from internal state: {val}")
            return val
        # 2. Если нет, пробуем получить из Dear PyGui (для ручного ввода)
        if key in self.inputs:
            val = dpg.get_value(self.inputs[key])
            print(f"BaseNode: Got input '{key}' from Dear PyGui UI: {val}")
            return val
        print(f"BaseNode: Input '{key}' not found in state or UI.")
        return None

    def set_output_value(self, key, value):
        """Сохраняет значение во внутреннее состояние и обновляет UI."""
        # Сохраняем внутрь
        self.state["outputs"][key] = value
        # Обновляем UI, если такой output существует
        if key in self.outputs:
            dpg.set_value(self.outputs[key], str(value))

    def set_input_value_from_link(self, key, value):
        """Устанавливает входное значение из другой ноды (через связь)."""
        # Сохраняем значение во внутреннее состояние
        self.state["inputs"][key] = value
        # --- НЕ ОБНОВЛЯЕМ UI ВХОДА ---
        # Это может привести к рекурсии или конфликту с пользовательским вводом
        # if key in self.inputs:
        #     dpg.set_value(self.inputs[key], str(value)) # <- УБРАНО
        print(f"BaseNode: Set input '{key}' from link to value {value}")

    # --- Метод для регистрации атрибутов ---
    def _register_attr(self, attr_id, attr_type, key):
        """
        Регистрирует атрибут в глобальной карте.
        attr_id: числовой ID атрибута
        attr_type: "input" или "output"
        key: строковый ключ ("a", "result", etc.)
        """
        BaseNode.attr_id_to_key_map[attr_id] = (self.node_id, attr_type, key)
        print(f"BaseNode: Registered attr {attr_id} -> ({self.node_id}, {attr_type}, {key})")


    #-------------------------------------Сохранение и загрузка-------------------------------------
    def to_dict(self) -> dict[str, any]:
        """Сохраняет состояние узла в словарь для сериализации"""
        state = {
            "label": getattr(self, 'label', type(self).__name__),
            "pos": self.pos,
            "inputs": {},
            "outputs": {},
            "internal_state": self.state  # Сохраняем внутреннее состояние
        }
        
        # Сохраняем значения входов
        for key, widget_id in self.inputs.items():
            try:
                value = dpg.get_value(widget_id)
                state["inputs"][key] = value
            except Exception:
                state["inputs"][key] = None
        
        # Сохраняем значения выходов
        for key, widget_id in self.outputs.items():
            try:
                value = dpg.get_value(widget_id)
                state["outputs"][key] = value
            except Exception:
                state["outputs"][key] = None
                
        return state
    
    def from_dict(self, data: dict[str, any]):
        """Восстанавливает состояние узла из словаря данных"""
        # Восстанавливаем позицию
        self.pos = data.get("pos", [100, 100])
        
        # Восстанавливаем значения входов
        for key, value in data.get("inputs", {}).items():
            if hasattr(self, 'inputs') and key in self.inputs:
                try:
                    dpg.set_value(self.inputs[key], value)
                except Exception:
                    pass
        
        # Восстанавливаем значения выходов
        for key, value in data.get("outputs", {}).items():
            if hasattr(self, 'outputs') and key in self.outputs:
                try:
                    dpg.set_value(self.outputs[key], value)
                except Exception:
                    pass
        
        # Восстанавливаем внутреннее состояние
        internal_state = data.get("internal_state", {})
        if internal_state:
            self.state = internal_state 