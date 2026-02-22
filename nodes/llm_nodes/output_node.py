# nodes/llm_nodes/output_node.py
import dearpygui.dearpygui as dpg
from ..base_node import BaseNode


class LLMOutputNode(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("LLM Output", parent, pos)
        self.output_field = None  # ссылка на UI-элемент чата

    def _create_inputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id:
            dpg.add_text("Input text:")
            self.inputs["text"] = dpg.add_input_text(
                label="##llm_output_text",
                multiline=True,
                height=60,
                width=250
            )
            self._register_attr(attr_id, "input", "text")

    def _create_outputs(self):
        # Статический атрибут для отображения статуса (не используется в связях)
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Status:", wrap=300)
            self.status = dpg.add_text("Ready", wrap=300)

    def process(self):
        text = self.get_input_value("text")
        if not text:
            return ""

        # Добавляем в чат (через глобальный менеджер чата — см. ниже)
        from nodes.llm_chat_manager import llm_chat_manager
        llm_chat_manager.add_response(text)

        dpg.set_value(self.status, "✅ Added to chat")
        return text

    def set_output_field(self, field_id):
        """Устанавливает ссылку на UI-элемент чата (вызывается из LLMTab)"""
        self.output_field = field_id
