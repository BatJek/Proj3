# nodes/llm_chat_manager.py

import dearpygui.dearpygui as dpg


class LLMChatManager:
    def __init__(self):
        self.messages = []  # [(role, text), ...], role: "user" | "assistant"
        self.chat_field_id = None
        self.user_input_id = None
        self.user_input_tag = None
        self.system_input_tag = None

    def set_chat_fields(self, user_input_id, chat_field_id):
        """Устанавливает ID UI-элементов"""
        self.user_input_id = user_input_id
        self.chat_field_id = chat_field_id

    def get_user_input_value(self):
        """Получает значение из поля пользовательского ввода по тегу"""
        if self.user_input_tag and dpg.does_item_exist(self.user_input_tag):
            return dpg.get_value(self.user_input_tag)
        elif self.user_input_id and dpg.does_item_exist(self.user_input_id):
            return dpg.get_value(self.user_input_id)
        return ""

    def get_system_prompt_value(self):
        """Получает значение из поля системного промпта по тегу"""
        if self.system_input_tag and dpg.does_item_exist(self.system_input_tag):
            return dpg.get_value(self.system_input_tag)
        return "You are a helpful assistant."

    def add_message(self, role: str, text: str):
        """Добавляет сообщение в историю и обновляет UI"""
        if not text:
            return

        self.messages.append((role, text))

        # Обновляем чат-поле
        if self.chat_field_id and dpg.does_item_exist(self.chat_field_id):
            current = dpg.get_value(self.chat_field_id)
            prefix = "👤 You: " if role == "user" else "🤖 Assistant: "
            new_entry = f"{prefix}{text}\n{'─' * 40}\n"
            dpg.set_value(self.chat_field_id, current + new_entry)

    def add_response(self, text: str):
        """Добавляет ответ нейросети"""
        self.add_message("assistant", text)

    def clear_chat(self):
        """Очищает чат"""
        self.messages.clear()
        if self.chat_field_id and dpg.does_item_exist(self.chat_field_id):
            dpg.set_value(self.chat_field_id, "")

    def get_context(self) -> list:
        """Возвращает историю в формате для LLM (list of dicts)"""
        return [{"role": role, "content": text} for role, text in self.messages]


# Глобальный экземпляр
llm_chat_manager = LLMChatManager()
