# nodes/execution_manager.py

import dearpygui.dearpygui as dpg
import threading
import time
from collections import defaultdict, deque
# Импортируем BaseNode, чтобы получить доступ к attr_id_to_key_map
from .base_node import BaseNode

class ExecutionManager:
    def __init__(self):
        self.node_instances = {}
        self.attribute_links = [] # [(source_attr_id, target_attr_id)]

        # Старые структуры
        self.node_dependencies_graph = defaultdict(set)
        # --- НОВОЕ: структуры для передачи данных ---
        # {target_attr_id: (source_node_id, source_output_key)}
        self.link_data_map = {}
        # ---

        self.execution_thread = None
        self.running = False
        self.execution_speed = 1.0

    def register_node(self, node_instance, node_id):
        self.node_instances[node_id] = node_instance
        print(f"ExecutionManager: Registered node {node_instance.label} with ID {node_id}")

    def unregister_node(self, node_id):
        if node_id in self.node_instances:
            del self.node_instances[node_id]
            print(f"ExecutionManager: Unregistered node ID {node_id}")

    def update_links(self, new_links):
        print(f"ExecutionManager: Updating links. Old count: {len(self.attribute_links)}, New count: {len(new_links)}")
        self.attribute_links = list(new_links)
        self._rebuild_dependency_structures()

    def _rebuild_dependency_structures(self):
        self.node_dependencies_graph.clear()
        # --- ОБНОВЛЕНИЕ НОВОЙ КАРТЫ ДАННЫХ ---
        self.link_data_map.clear()
        # ---

        for source_attr_id, target_attr_id in self.attribute_links:
            # Получаем информацию о source_attr из BaseNode.attr_id_to_key_map
            source_info = BaseNode.attr_id_to_key_map.get(source_attr_id)
            target_info = BaseNode.attr_id_to_key_map.get(target_attr_id)

            if source_info and target_info:
                source_node_id, source_attr_type, source_key = source_info
                target_node_id, target_attr_type, target_key = target_info

                # Проверяем, что типы атрибутов корректны для соединения
                if source_attr_type == "output" and target_attr_type == "input":
                    # source_node_id -> target_node_id
                    self.node_dependencies_graph[source_node_id].add(target_node_id)
                    # --- ЗАПОЛНЯЕМ НОВУЮ КАРТУ ДАННЫХ ---
                    self.link_data_map[target_attr_id] = (source_node_id, source_key, target_key)
                    print(f"ExecutionManager: Linked {source_node_id}.{source_key} -> {target_node_id}.{target_key}")
                else:
                    print(f"ExecutionManager: Invalid link direction or types: {source_attr_type} -> {target_attr_type}")
            else:
                print(f"ExecutionManager: Could not resolve link endpoints for IDs {source_attr_id} -> {target_attr_id}")

        print(f"ExecutionManager: Dependency graph and data map rebuilt.")


    def _propagate_data(self):
        """Передаёт данные от выходов к входам по связям."""
        for target_attr_id, (source_node_id, source_output_key, target_input_key) in self.link_data_map.items():
            source_node_instance = self.node_instances.get(source_node_id)

            if source_node_instance:
                # Получаем значение из выхода источника
                source_value = source_node_instance.state["outputs"].get(source_output_key)
                if source_value is not None:
                    # Найдём target_node_instance и target_input_key
                    target_info = BaseNode.attr_id_to_key_map.get(target_attr_id)
                    if target_info:
                        _, _, resolved_target_input_key = target_info
                        # Найдём экземпляр target ноды
                        target_node_instance = self.node_instances.get(target_info[0]) # target_node_id
                        if target_node_instance:
                            # Устанавливаем значение во вход получателя
                            target_node_instance.set_input_value_from_link(resolved_target_input_key, source_value)
                            print(f"ExecutionManager: Propagated '{source_value}' from {source_node_instance.label}.{source_output_key} to {target_node_instance.label}.{resolved_target_input_key}")
                        else:
                            print(f"ExecutionManager: Target node instance for {target_info[0]} not found.")
                    else:
                        print(f"ExecutionManager: Target info for attr ID {target_attr_id} not found in BaseNode map.")
                else:
                    print(f"ExecutionManager: Source output value for {source_node_instance.label}.{source_output_key} is None.")
            else:
                print(f"ExecutionManager: Source node instance for ID {source_node_id} not found.")


    def _topological_sort(self):
        in_degree = {node_id: 0 for node_id in self.node_instances}
        for node_id, dependents in self.node_dependencies_graph.items():
            for dep_node_id in dependents:
                if dep_node_id in in_degree:
                    in_degree[dep_node_id] += 1

        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_order = []

        while queue:
            current_node_id = queue.popleft()
            sorted_order.append(current_node_id)

            for dependent_node_id in self.node_dependencies_graph.get(current_node_id, set()):
                if dependent_node_id in in_degree:
                    in_degree[dependent_node_id] -= 1
                    if in_degree[dependent_node_id] == 0:
                        queue.append(dependent_node_id)

        if len(sorted_order) != len(self.node_instances):
            print("ExecutionManager: WARNING - Cycle detected in node dependencies.")
            return []

        return sorted_order

    def _execute_loop(self):
        while self.running:
            try:
                execution_order = self._topological_sort()
                if not execution_order:
                    time.sleep(1.0 / max(1, self.execution_speed))
                    continue

                # --- ПЕРЕДАЁМ ДАННЫЕ ---
                self._propagate_data()
                # ---

                print(f"ExecutionManager: Executing {len(execution_order)} nodes in order: {execution_order}")
                for node_id in execution_order:
                    if not self.running:
                        break
                    node_instance = self.node_instances.get(node_id)
                    if node_instance:
                        print(f"ExecutionManager: Processing node {node_instance.label} (ID: {node_id})")
                        try:
                            node_instance.process()
                        except Exception as e:
                            print(f"ExecutionManager: Error processing node {node_instance.label} (ID: {node_id}): {e}")
                    else:
                        print(f"ExecutionManager: WARNING - Node instance for ID {node_id} not found.")

                time.sleep(1.0 / max(1, self.execution_speed))

            except Exception as e:
                print(f"ExecutionManager: Critical error in execution loop: {e}")
                self.stop_execution()
                break

    def start_execution(self):
        if not self.running and self.execution_thread is None:
            self.running = True
            self.execution_thread = threading.Thread(target=self._execute_loop, daemon=True)
            self.execution_thread.start()
            print("ExecutionManager: Started execution loop.")
        else:
            print("ExecutionManager: Execution is already running or thread is active.")

    def stop_execution(self):
        if self.running:
            self.running = False
            if self.execution_thread:
                self.execution_thread.join(timeout=2)
                self.execution_thread = None
            print("ExecutionManager: Stopped execution loop.")
        else:
            print("ExecutionManager: Execution is not running.")

    def set_execution_speed(self, speed):
        self.execution_speed = max(0.1, speed)
        print(f"ExecutionManager: Set execution speed to {speed} Hz")

execution_manager = ExecutionManager()