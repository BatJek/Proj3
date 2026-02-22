import dearpygui.dearpygui as dpg
from .math_nodes.math_simple import AddNode, MultiplyNode
from .logic_nodes.logic_simple import If_statement_node
from .text.Simple import TextViewerNode
# Добавляем импорт LLaMA ноды
from .llm_nodes.llama_node import LLaMANode
from .vector_db.qdrant_nodes import QdrantAddNode, QdrantSearchNode
from .llm_nodes.output_node import LLMOutputNode
from .llm_nodes.user_input_prompt import UserInputPromptNode
from .llm_nodes.system_prompt import SystemPromptNode

NODE_REGISTRY = {
    "Math": {
        "Add": {
            "class": AddNode,
            "node_store": "REGISTRY",
            "description": "Сложение двух чисел",
            "category": "Math"
        },
        "Multiply": {
            "class": MultiplyNode,
            "node_store": "REGISTRY",
            "description": "Умножение двух чисел",
            "category": "Math"
        },
    },
    "Logic": {
        "If": {
            "class": If_statement_node,
            "node_store": "REGISTRY",
            "description": "Логическое если",
            "category": "Logic"  # ← исправлено: было "Math"
        },
    },
    "LLM": {
        "LLaMA": {
            "class": LLaMANode,
            "node_store": "REGISTRY",
            "description": "LLaMA модель для генерации текста",
            "category": "LLM"
        },
        "LLM Output": {
            "class": LLMOutputNode,
            "node_store": "REGISTRY",
            "description": "Добавляет текст в чат как ответ нейросети",
            "category": "LLM"
        },
        "User Input Prompt": {
            "class": UserInputPromptNode,
            "node_store": "REGISTRY",
            "description": "Позволяет пользователю ввести текстовый запрос",
            "category": "LLM"
        },
        "System Prompt": {
            "class": SystemPromptNode,
            "node_store": "REGISTRY",
            "description": "Задает системное сообщение для модели",
            "category": "LLM"
        },
    },
    "Text": {
        "Output": {
            "class": TextViewerNode,
            "node_store": "REGISTRY",
            "description": "Вывод текста",
            "category": "Text"
        },
    },
    "Vector DB": {
        "Qdrant Add": {
            "class": QdrantAddNode,
            "node_store": "REGISTRY",
            "description": "Добавление векторов в Qdrant базу данных",
            "category": "Vector DB"
        },
        "Qdrant Search": {
            "class": QdrantSearchNode,
            "node_store": "REGISTRY",
            "description": "Поиск похожих векторов в Qdrant",
            "category": "Vector DB"
        },
    },
}

created_nodes = {}  # Словарь: {node_id: instance}

# === ГЛОБАЛЬНЫЕ ТЕМЫ ДЛЯ РАЗНЫХ ТИПОВ НОД ===
qdrant_theme = None
llm_theme = None
math_theme = None

def init_themes():
    """Инициализация тем для разных типов нод"""
    global qdrant_theme, llm_theme, math_theme
    
    # 🔵 Тема для Qdrant нод
    with dpg.theme() as qdrant_theme:
        with dpg.theme_component(dpg.mvNode):
            # Закругление рамки
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
            # Цвет заголовка (голубой для баз данных)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (66, 135, 245, 255), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (51, 119, 230, 255), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (36, 103, 215, 255), category=dpg.mvThemeCat_Nodes)
            # Цвет фона
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, (30, 30, 40, 255), category=dpg.mvThemeCat_Nodes)
    
    # 🟣 Тема для LLM нод
    with dpg.theme() as llm_theme:
        with dpg.theme_component(dpg.mvNode):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (138, 43, 226, 255), category=dpg.mvThemeCat_Nodes)  # Фиолетовый
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (123, 36, 211, 255), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (108, 29, 196, 255), category=dpg.mvThemeCat_Nodes)
    
    # 🟢 Тема для математических нод
    with dpg.theme() as math_theme:
        with dpg.theme_component(dpg.mvNode):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (46, 204, 113, 255), category=dpg.mvThemeCat_Nodes)  # Зелёный
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (39, 174, 96, 255), category=dpg.mvThemeCat_Nodes)
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (32, 153, 80, 255), category=dpg.mvThemeCat_Nodes)

def register_node(instance):
    """Регистрирует экземпляр ноды."""
    if instance.node_id:
        created_nodes[instance.node_id] = instance
        print(f"Registered node: {instance.label} with ID {instance.node_id}")
        
        # Автоматически применяем тему при регистрации
        apply_theme_to_node(instance)

def apply_theme_to_node(instance):
    """Применяет тему к конкретной ноде на основе её типа"""
    if not instance.node_id:
        return
    
    # Определяем тип ноды по классу
    if isinstance(instance, (QdrantAddNode, QdrantSearchNode)):
        if qdrant_theme:
            dpg.bind_item_theme(instance.node_id, qdrant_theme)
            print(f"🎨 Applied Qdrant theme to {instance.label}")
    
    elif isinstance(instance, (LLaMANode, UserInputPromptNode, SystemPromptNode)):
        if llm_theme:
            dpg.bind_item_theme(instance.node_id, llm_theme)
            print(f"🎨 Applied LLM theme to {instance.label}")
    
    elif isinstance(instance, (AddNode, MultiplyNode)):
        if math_theme:
            dpg.bind_item_theme(instance.node_id, math_theme)
            print(f"🎨 Applied Math theme to {instance.label}")

def change_theme():
    """Применяет темы ко всем зарегистрированным нодам"""
    print("🔄 Applying themes to all nodes...")
    for node_id, instance in created_nodes.items():
        apply_theme_to_node(instance)
    print("✅ Themes applied")

def unregister_node(node_id):
    """Удаляет экземпляр ноды из реестра."""
    if node_id in created_nodes:
        del created_nodes[node_id]
        print(f"Unregistered node ID {node_id}")

def get_node_instance(node_id):
    """Получает экземпляр ноды по ID."""
    return created_nodes.get(node_id)


def create_node_instance(node_name, **kwargs):
    """
    Создает экземпляр ноды по имени.
    
    Args:
        node_name (str): Имя ноды (например, 'Add', 'Multiply', 'LLaMA')
        **kwargs: Дополнительные аргументы для передачи в конструктор ноды
    
    Returns:
        instance: Экземпляр ноды или None, если нода не найдена
    """
    # Ищем ноду по всем категориям
    for category, nodes in NODE_REGISTRY.items():
        if node_name in nodes:
            node_info = nodes[node_name]
            node_class = node_info["class"]
            
            # Создаем экземпляр ноды с переданными аргументами
            instance = node_class(**kwargs)
            return instance
    
    print(f"⚠️ Node '{node_name}' not found in registry")
    return None


