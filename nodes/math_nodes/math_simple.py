# nodes/math_nodes/math_simple.py
from ..base_node import BaseNode
import dearpygui.dearpygui as dpg

class AddNode(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("Add", parent, pos)

    def _create_inputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_a:
            self.inputs["a"] = dpg.add_input_float(label="A", default_value=0.0, width=150)
        self._register_attr(attr_id_a, "input", "a")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_b:
            self.inputs["b"] = dpg.add_input_float(label="B", default_value=0.0, width=150)
        self._register_attr(attr_id_b, "input", "b")

    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_out:
            self.outputs["result"] = dpg.add_text("0.0")
        self._register_attr(attr_id_out, "output", "result")

    def process(self):
        a = self.get_input_value("a")
        b = self.get_input_value("b")
        print(f"AddNode {self.label} processing: {a} + {b}")
        if a is not None and b is not None:
            result = a + b
            self.set_output_value("result", result)
            return result
        else:
            print(f"AddNode {self.label}: Input values are None, cannot compute.")
            return 0.0
    
class MultiplyNode(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("Multiply", parent, pos)

    def _create_inputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_a:
            self.inputs["a"] = dpg.add_input_float(label="A", default_value=0.0, width=150)
        # РЕГИСТРИРУЕМ
        self._register_attr(attr_id_a, "input", "a")

        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_b:
            self.inputs["b"] = dpg.add_input_float(label="B", default_value=0.0, width=150)
        # РЕГИСТРИРУЕМ
        self._register_attr(attr_id_b, "input", "b")


    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_out:
            self.outputs["result"] = dpg.add_text("0.0")
        # РЕГИСТРИРУЕМ
        self._register_attr(attr_id_out, "output", "result")


    def process(self):
        a = self.get_input_value("a")
        b = self.get_input_value("b")
        print(f"MultiplyNode {self.label} processing: {a} * {b}")
        if a is not None and b is not None:
            result = a * b
            self.set_output_value("result", result)
            return result
        else:
            print(f"MultiplyNode {self.label}: Input values are None, cannot compute.")
            return 0.0 # Возвращаем 0.0 или None, если входы не определены