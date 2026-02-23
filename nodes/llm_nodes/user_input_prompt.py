from ..base_node import BaseNode
import dearpygui.dearpygui as dpg


class UserInputPromptNode(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("User Input Prompt", parent, pos)
        self.value = ""
        
    def _create_inputs(self):
        # No inputs for this node since it's a source
        pass
    
    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id:
            dpg.add_text("User Prompt:")
            self.outputs["user_prompt"] = dpg.add_input_text(
                label="##user_prompt", 
                multiline=True, 
                readonly=True, 
                height=100, 
                width=200,
                default_value=self.value
            )
            self._register_attr(attr_id, "output", "user_prompt")
    
    def process(self):
        """Process node - returns the current user input value"""
        return self.value
        
    def set_value(self, value):
        """Set the value of the user input prompt"""
        self.value = value
        if "user_prompt" in self.outputs and dpg.does_item_exist(self.outputs["user_prompt"]):
            dpg.set_value(self.outputs["user_prompt"], value)
    
    def to_dict(self):
        """Serialize node state"""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "pos": dpg.get_item_pos(self.self.node_id),
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data, parent="node_editor"):
        """Deserialize node state"""
        node = cls(parent, data["pos"])
        node.value = data.get("value", "")
        if "user_prompt" in node.outputs and dpg.does_item_exist(node.outputs["user_prompt"]):
            dpg.set_value(node.outputs["user_prompt"], node.value)
        return node