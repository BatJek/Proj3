# nodes/tabs/llm_tab.py
import dearpygui.dearpygui as dpg
from nodes.llm_chat_manager import llm_chat_manager


class LLMTab:
    def create(self, parent_window):
        with dpg.tab(label="  LLM Chat  ", parent=parent_window):
            # Панель управления чатом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Clear Chat",
                    callback=lambda: llm_chat_manager.clear_chat()
                )
                dpg.add_spacer(width=10)
                dpg.add_text("Chat History:")

            # Поля ввода для промптов
            with dpg.group():
                # Пользовательский промпт
                dpg.add_text("User Prompt:")
                user_input = dpg.add_input_text(
                    tag="llm_user_input",
                    multiline=True,
                    height=80,
                    width=-1
                )
                
                # Системный промпт
                dpg.add_spacer(height=10)
                dpg.add_text("System Prompt:")
                system_input = dpg.add_input_text(
                    tag="llm_system_prompt",
                    multiline=True,
                    height=80,
                    width=-1,
                    default_value="You are a helpful assistant."
                )

                # Кнопка "Отправить" (отправляет в чат и вызывает LLM-ноду)
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Send to Chat",
                        callback=lambda: self._on_send_to_chat(user_input)
                    )
                    dpg.add_spacer(width=10)
                    dpg.add_button(
                        label="Generate (via LLM)",
                        callback=lambda: self._on_generate_from_chat()
                    )

            # Поле вывода (история чата)
            with dpg.group():
                dpg.add_text("Chat Output:")
                chat_field = dpg.add_input_text(
                    tag="llm_chat_output",
                    multiline=True,
                    readonly=True,
                    height=300,
                    width=-1
                )

                # Сохраняем ссылки в менеджер чата
                llm_chat_manager.set_chat_fields(user_input, chat_field)
                
                # Сохраняем теги полей промптов
                llm_chat_manager.user_input_tag = "llm_user_input"
                llm_chat_manager.system_input_tag = "llm_system_prompt"

    def _on_send_to_chat(self, user_input_id):
        """Добавляет сообщение пользователя в чат"""
        text = dpg.get_value(user_input_id).strip()
        if not text:
            return

        llm_chat_manager.add_message("user", text)
        dpg.set_value(user_input_id, "")  # очистить поле

    def _on_generate_from_chat(self):
        """Запускает генерацию на основе истории чата"""
        from nodes.registry import created_nodes
        from nodes.llm_nodes.llama_node import LLaMANode
        
        print(f"🔍 created_nodes = {list(created_nodes.keys())}")  # ← добавлено

        # Ищем первую загруженную LLaMA-ноду
        for node_id, instance in created_nodes.items():
            if isinstance(instance, LLaMANode) and instance.llm:
                context = llm_chat_manager.get_context()
                prompt = "\n".join(
                    f"{msg['role'].capitalize()}: {msg['content']}"
                    for msg in context
                )
                # Запускаем генерацию (можно обернуть в поток)
                instance.last_prompt = prompt
                instance.generate_background(prompt)
                return

        dpg.set_value("llm_chat_output", "⚠️ LLaMA-нода не найдена или модель не загружена.")
