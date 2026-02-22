# nodes/math_nodes/math_simple.py
from ..base_node import BaseNode
import dearpygui.dearpygui as dpg

class If_statement_node(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("Add", parent, pos)
    
    def _create_inputs(self):
        with dpg.node_attribute(tag=f"{self.node_id}_input_a", attribute_type=dpg.mvNode_Attr_Input):
            self.inputs["a"] = dpg.add_input_float(label="A", default_value=0.0, width=150)
        
        with dpg.node_attribute(tag=f"{self.node_id}_input_b", attribute_type=dpg.mvNode_Attr_Input):
            self.inputs["b"] = dpg.add_input_float(label="B", default_value=0.0, width=150)
    
    def _create_outputs(self):
        with dpg.node_attribute(tag=f"{self.node_id}_output", attribute_type=dpg.mvNode_Attr_Output):
            self.outputs["result"] = dpg.add_text("0.0")
    
    def process(self):
        a = dpg.get_value(self.inputs["a"])
        b = dpg.get_value(self.inputs["b"])
        result = a + b
        dpg.set_value(self.outputs["result"], f"{result:.2f}")
        return result