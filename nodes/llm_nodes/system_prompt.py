from ..base_node import BaseNode
import dearpygui.dearpygui as dpg


class SystemPromptNode(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("System Prompt", parent, pos)
        self.value = "You are a helpful assistant."
        
    def _create_inputs(self):
        # No inputs for this node since it's a source
        pass
    
    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id:
            dpg.add_text("System Prompt:")
            self.outputs["system_prompt"] = dpg.add_input_text(
                label="##system_prompt", 
                multiline=True, 
                readonly=True, 
                height=100, 
                width=200,
                default_value=self.value
            )
            self._register_attr(attr_id, "output", "system_prompt")
    
    def process(self):
        """Process node - returns the current system prompt value"""
        return self.value
        
    def set_value(self, value):
        """Set the value of the system prompt"""
        self.value = value
        if "system_prompt" in self.outputs and dpg.does_item_exist(self.outputs["system_prompt"]):
            dpg.set_value(self.outputs["system_prompt"], value)
    
    def to_dict(self):
        """Serialize node state"""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "pos": dpg.get_item_pos(self.node_tag),
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data, parent="node_editor"):
        """Deserialize node state"""
        node = cls(parent, data["pos"])
        node.value = data.get("value", "You are a helpful assistant.")
        if "system_prompt" in node.outputs and dpg.does_item_exist(node.outputs["system_prompt"]):
            dpg.set_value(node.outputs["system_prompt"], node.value)
        return node