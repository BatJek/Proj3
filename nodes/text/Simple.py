import dearpygui.dearpygui as dpg
from ..base_node import BaseNode

class TextViewerNode(BaseNode):
    def __init__(self, tag_suffix="_stream", parent="node_editor", pos=None):
        super().__init__("LLaMA", parent, pos)
        self.node_tag = f"viewer_node_{tag_suffix}"
        self.input_tag = f"text_display_{tag_suffix}"
        self.width = 400
        self.height = 300

    def add_node(self, parent_editor):
        with dpg.node(label="Stream Viewer", tag=self.node_tag, parent=parent_editor):
            # Входной атрибут (пин) для логической связи между нодами
            with dpg.node_attribute(label="Input", attribute_type=dpg.mvNode_Attr_Input):
                # Многострочное поле только для чтения
                dpg.add_input_text(
                    tag=self.input_tag,
                    multiline=True,
                    readonly=True, 
                    width=self.width,
                    height=self.height,
                    hint="Ожидание данных...",
                    # Флаг tab_input позволяет копировать текст, но не дает редактировать
                )
            
            # Кнопка быстрой очистки
            dpg.add_button(label="Clear", callback=lambda: dpg.set_value(self.input_tag, ""))

    def update_text(self, new_content):
        """Метод для внешнего вызова из потока генерации"""
        if dpg.does_item_exist(self.input_tag):
            dpg.set_value(self.input_tag, new_content)
            
            # Автоматический скролл вниз
            # В DPG для этого нужно установить фокус или прокрутить через функцию
            dpg.set_y_scroll(self.input_tag, dpg.get_y_scroll_max(self.input_tag))


    def _create_inputs(self):
        # Реализация входов
        pass
        
    def _create_outputs(self):  
        # Реализация выходов
        pass
        
    def process(self):
        # Реализация обработки
        pass
