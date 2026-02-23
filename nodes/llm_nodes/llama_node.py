from ..base_node import BaseNode
import dearpygui.dearpygui as dpg
from llama_cpp import Llama
import threading
import time
import json
import os
import numpy as np

class LLaMANode(BaseNode):
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("LLaMA", parent, pos)
        self.llm = None
        self.model_path = ""
        self.is_loading = False
        self.is_generating = False
        self.parameters = {
            "temperature": 0.7,
            "max_tokens": 256,
            "top_p": 0.9,
            "n_gpu_layers": 35,
            "n_ctx": 2048,
            "n_threads": 8
        }
        self.last_output = ""
        self.last_prompt = ""
        
    def _create_inputs(self):
        print(f"🔧 Creating inputs for {self.label}")  # ← добавлено
        # Input for user prompt
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_prompt:
            dpg.add_text("Prompt:")
            self.inputs["prompt"] = dpg.add_input_text(label="##prompt", multiline=True, height=80, width=250, default_value="Hello!")
            self._register_attr(attr_id_prompt, "input", "prompt")
        
        # Input for system prompt
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_sys_prompt:
            dpg.add_text("System Prompt:")
            self.inputs["system_prompt"] = dpg.add_input_text(label="##sys_prompt", multiline=True, height=80, width=250, default_value="You are a helpful assistant.")
            self._register_attr(attr_id_sys_prompt, "input", "system_prompt")
        
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_button(label="Load Model", callback=lambda s, a, u=self: self.show_model_dialog())
            dpg.add_same_line()
            dpg.add_button(label="Generate", callback=lambda s, a, u=self: self.start_generation())
            dpg.add_separator()
            
            # Параметры генерации
            dpg.add_text("Temperature:")
            self.temp_slider = dpg.add_slider_float(default_value=self.parameters["temperature"], 
                                                  min_value=0.0, max_value=2.0, width=200,
                                                  callback=lambda s, a, u=self: self.update_parameter("temperature", a))
            
            dpg.add_text("Max Tokens:")
            self.max_tokens_slider = dpg.add_slider_int(default_value=self.parameters["max_tokens"],
                                                      min_value=1, max_value=65536, width=200,
                                                      callback=lambda s, a, u=self: self.update_parameter("max_tokens", a))
            
            dpg.add_text("Top P:")
            self.top_p_slider = dpg.add_slider_float(default_value=self.parameters["top_p"],
                                                    min_value=0.0, max_value=1.0, width=200,
                                                    callback=lambda s, a, u=self: self.update_parameter("top_p", a))
    
    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_output:
            dpg.add_text("Result:")
            self.outputs["result"] = dpg.add_input_text(label="##result", multiline=True, readonly=True, height=100, width=350)
            self._register_attr(attr_id_output, "output", "result")
        
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            self.status_text = dpg.add_text("Status: Model not loaded")
            self.progress_bar = dpg.add_progress_bar(default_value=0.0, width=200, show=False)
    
    def show_model_dialog(self):
        """Показать диалог выбора модели"""
        if not dpg.does_item_exist("model_dialog"):
            with dpg.file_dialog(directory_selector=False, show=False, callback=self.model_selected,
                               tag="model_dialog", width=700, height=400):
                dpg.add_file_extension("GGUF Files (*.gguf){.gguf}", color=(0, 255, 0, 255))
                dpg.add_file_extension("All Files (*.*){.*}", color=(255, 255, 255, 255))
        
        dpg.show_item("model_dialog")
    
    def model_selected(self, sender, app_data):
        """Обработка выбора модели"""
        self.model_path = app_data["file_path_name"]
        dpg.set_value(self.status_text, f"Status: Loading model...")
        dpg.configure_item(self.progress_bar, show=True)
        
        # Загрузка в фоновом потоке
        threading.Thread(target=self.load_model_background, daemon=True).start()
    
    def load_model_background(self):
            try:
                self.is_loading = True

                for i in range(1, 101):
                    time.sleep(0.05)
                    dpg.configure_item(self.progress_bar, default_value=i/100)

                # 🔥 Добавляем явный чат-тюнинг
                chat_template = """{{ bos_token }}
                                {% for message in messages %}
                                    {% if message['role'] == 'user' %}
                                        {{ '[INST] ' + message['content'] + ' [/INST]' }}
                                    {% elif message['role'] == 'assistant' %}
                                        {{ message['content'] + eos_token }}
                                    {% else %}
                                        {{ message['content'] }}
                                    {% endif %}
                                {% endfor %}"""

                self.llm = Llama(
                    model_path=self.model_path,
                    n_gpu_layers=self.parameters["n_gpu_layers"],
                    n_ctx=self.parameters["n_ctx"],
                    n_threads=self.parameters["n_threads"],
                    verbose=False,
                    chat_format="chatml",  # ← попробуйте "chatml" или "qwen2_vl"
                    # Если не помогает — укажите кастомный шаблон:
                    # chat_template=chat_template
                )

                dpg.set_value(self.status_text, f"Status: Model loaded: {os.path.basename(self.model_path)}")
                print(f"✅ Модель успешно загружена: {self.model_path}")

            except Exception as e:
                error_msg = f"Status: Error loading model: {str(e)}"
                dpg.set_value(self.status_text, error_msg)
                print(f"❌ Ошибка загрузки модели: {e}")

    
    def update_parameter(self, param_name, value):
        """Обновление параметра"""
        self.parameters[param_name] = value
    
    
    def start_generation(self):
        """Начать генерацию в фоновом потоке"""
        if not self.llm:
            dpg.set_value(self.status_text, "Status: Model not loaded. Please load a model first.")
            return
        
        prompt = self.get_input_value("prompt")
        if not prompt:
            prompt = "Hello!"
        
        self.last_prompt = prompt
        dpg.set_value(self.status_text, "Status: Generating...")
        dpg.configure_item(self.progress_bar, show=True)
        
        threading.Thread(target=self.generate_background, args=(prompt,), daemon=True).start()
    
    def generate_background(self, prompt):
        """Генерация в фоновом потоке с разделением на System и User промпты"""
        try:
            self.is_generating = True
            dpg.set_value(self.outputs["result"], "")
            dpg.configure_item(self.progress_bar, show=True, default_value=0.05)
            
            # Получаем системный промпт (предположим, у вас есть такой вход в ноде)
            # Если входа нет, можно задать значение по умолчанию
            system_message = self.get_input_value("system_prompt") or "You are a helpful assistant."
            user_message = prompt
            
            if self.llm:
                # Используем create_chat_completion для автоматического форматирования ChatML
                stream = self.llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=self.parameters["temperature"],
                    max_tokens=self.parameters["max_tokens"],
                    top_p=self.parameters["top_p"],
                    stop=["<|im_end|>", "<|endoftext|>", "###"],
                    stream=True  # Активируем поток
                )
                
                full_text = ""
                for chunk in stream:
                    # В chat-режиме дельта лежит в ключе 'delta'
                    if "content" in chunk["choices"][0]["delta"]:
                        token = chunk["choices"][0]["delta"]["content"]
                        full_text += token
                        
                        # Обновляем DearPyGui в реальном времени
                        dpg.set_value(self.outputs["result"], full_text)
                        
                        # Небольшой визуальный прогресс
                        progress = min(0.95, 0.05 + (len(full_text) / self.parameters["max_tokens"]))
                        dpg.set_value(self.progress_bar, progress)

                self.last_output = full_text
            
            dpg.set_value(self.status_text, "Status: Generation complete")
            
        except Exception as e:
            error_msg = f"Status: Error: {str(e)}"
            dpg.set_value(self.status_text, error_msg)
            dpg.set_value(self.outputs["result"], f"Error: {str(e)}")
            print(f"❌ Ошибка: {e}")
        finally:
            self.is_generating = False
            dpg.configure_item(self.progress_bar, show=False)

    
    def process(self):
        """Обработка ноды - вызывается менеджером выполнения"""
        print(f"LLaMANode {self.label} processing")
        return self.last_output
    
    def to_dict(self):
        """Сериализация состояния ноды"""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "pos": dpg.get_item_pos(self.node_id),
            "model_path": self.model_path,
            "parameters": self.parameters.copy(),
            "last_prompt": self.last_prompt,
            "last_output": self.last_output,
            "inputs": {key: dpg.get_value(widget) for key, widget in self.inputs.items()},
            "outputs": {key: dpg.get_value(widget) for key, widget in self.outputs.items()}
        }
    
    @classmethod
    def from_dict(cls, data, parent="node_editor"):
        """Десериализация состояния ноды"""
        node = cls(parent, data["pos"])
        
        # Восстанавливаем состояние
        node.model_path = data.get("model_path", "")
        node.parameters = data.get("parameters", node.parameters)
        node.last_prompt = data.get("last_prompt", "")
        node.last_output = data.get("last_output", "")
        
        # Восстанавливаем UI значения
        for key, value in data.get("inputs", {}).items():
            if key in node.inputs and dpg.does_item_exist(node.inputs[key]):
                dpg.set_value(node.inputs[key], value)
        
        for key, value in data.get("outputs", {}).items():
            if key in node.outputs and dpg.does_item_exist(node.outputs[key]):
                dpg.set_value(node.outputs[key], value)
        
        # Пытаемся загрузить модель, если путь существует
        if node.model_path and os.path.exists(node.model_path):
            try:
                threading.Thread(target=node.load_model_background, daemon=True).start()
            except Exception as e:
                print(f"Не удалось автоматически загрузить модель: {e}")
        
        return node