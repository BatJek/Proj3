# nodes\vector_db\qdrant_nodes.py
import dearpygui.dearpygui as dpg
from ..base_node import BaseNode
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
import json
import os
import uuid
import tkinter as tk
from tkinter import filedialog

class QdrantAddNode(BaseNode):
    """Нода для добавления векторов в Qdrant в локальном режиме"""
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("Qdrant Add", parent, pos)
        self.client = None
        self.collection_name = "default_collection"
        self.vector_size = 1536
        self.distance = Distance.COSINE
        self.is_connected = False
        self.last_result = ""
        self.max_node_width = 350
        self.mode = "In-Memory"
        self.storage_path = "./qdrant_storage"
        self.storage_attr = None
        self.mode_combo = None
        self.storage_path_input = None

    def _create_inputs(self):
        # Режим работы Qdrant
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Qdrant Mode", wrap=300)
            self.mode_combo = dpg.add_combo(
                items=["In-Memory", "Local Storage"],
                default_value=self.mode,
                width=200,
                callback=lambda s, a, u=self: self.update_mode(a)
            )
            
        # Путь к локальному хранилищу
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static) as self.storage_attr:
            dpg.add_text("Storage Path:", wrap=300)
            self.storage_path_input = dpg.add_input_text(
                label="##storage_path",
                default_value=self.storage_path,
                width=min(200, self.max_node_width - 40)
            )
            dpg.add_button(
                label="Browse",
                callback=lambda s, a, u=self: self.browse_storage_path()
            )
            
        dpg.add_button(
            label="Connect",
            callback=lambda s, a, u=self: self.connect_to_qdrant()
        )
        dpg.add_separator()
        
        # Collection name
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_collection:
            dpg.add_text("Collection Name:", wrap=300)
            self.inputs["collection_name"] = dpg.add_input_text(
                label="##collection",
                default_value="documents",
                width=min(250, self.max_node_width - 40),
                wrap=True
            )
            self._register_attr(attr_id_collection, "input", "collection_name")
            
        # Vector size
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_vector_size:
            dpg.add_text("Vector Size:", wrap=300)
            self.inputs["vector_size"] = dpg.add_input_int(
                label="##vector_size",
                default_value=1536,
                min_value=1,
                width=min(200, self.max_node_width - 40),
            )
            self._register_attr(attr_id_vector_size, "input", "vector_size")
            
        # Vector input
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_vector:
            dpg.add_text("Vector (JSON array):", wrap=300)
            self.inputs["vector"] = dpg.add_input_text(
                label="##vector",
                multiline=True,
                height=60,
                wrap=True,
                width=min(250, self.max_node_width - 40),
                hint="[0.1, 0.2, 0.3, ...]"
            )
            self._register_attr(attr_id_vector, "input", "vector")
            
        # Payload
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_payload:
            dpg.add_text("Payload (JSON):", wrap=300)
            self.inputs["payload"] = dpg.add_input_text(
                label="##payload",
                multiline=True,
                height=80,
                wrap=True,
                width=min(250, self.max_node_width - 40),
                hint='{"text": "example", "id": 1}'
            )
            self._register_attr(attr_id_payload, "input", "payload")
            
        # Add button
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_button(label="Add Point", callback=lambda s, a, u=self: self.add_point())
            
        self.update_mode(self.mode)

    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_status:
            dpg.add_text("Status:", wrap=300)
            self.outputs["status"] = dpg.add_text("Not connected", wrap=300)
            self._register_attr(attr_id_status, "output", "status")
            
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_point_id:
            dpg.add_text("Point ID:", wrap=300)
            self.outputs["point_id"] = dpg.add_text("N/A", wrap=300)
            self._register_attr(attr_id_point_id, "output", "point_id")
            
        if hasattr(self, 'node_id') and self.node_id:
            dpg.set_item_width(self.node_id, self.max_node_width)

    def update_mode(self, mode):
        """Показывает/скрывает поле для пути к хранилищу"""
        self.mode = mode
        if self.storage_attr:
            if mode == "Local Storage":
                dpg.show_item(self.storage_attr)
            else:
                dpg.hide_item(self.storage_attr)

    def browse_storage_path(self):
        """Диалог выбора пути к хранилищу"""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory()
        if path:
            dpg.set_value(self.storage_path_input, path)
            self.storage_path = path

    def connect_to_qdrant(self):
        """Подключение к Qdrant в локальном режиме"""
        try:
            mode = dpg.get_value(self.mode_combo)
            if mode == "In-Memory":
                self.client = QdrantClient(location=":memory:")
                status_text = "Connected to in-memory Qdrant"
            else:
                self.storage_path = dpg.get_value(self.storage_path_input)
                self.client = QdrantClient(path=self.storage_path)
                status_text = f"Connected to local Qdrant at {self.storage_path}"
                
            self.is_connected = True
            dpg.set_value(self.outputs["status"], status_text)
            print(f"✅ {status_text}")
        except Exception as e:
            error_text = f"Error: {str(e)}"
            dpg.set_value(self.outputs["status"], error_text)
            print(f"❌ Ошибка подключения: {e}")
            self.is_connected = False

    def add_point(self):
        """Добавить точку в коллекцию"""
        if not self.is_connected or not self.client:
            dpg.set_value(self.outputs["status"], "Not connected. Click 'Connect' first.")
            return
            
        try:
            collection_name = self.get_input_value("collection_name") or "documents"
            vector_size = self.get_input_value("vector_size") or 1536
            
            vector_str = self.get_input_value("vector")
            if not vector_str:
                dpg.set_value(self.outputs["status"], "Error: Vector is empty")
                return
                
            try:
                vector = json.loads(vector_str)
                if not isinstance(vector, list):
                    raise ValueError("Vector must be a list")
                if len(vector) != vector_size:
                    print(f"⚠️ Warning: Expected vector size {vector_size}, got {len(vector)}")
            except json.JSONDecodeError as e:
                dpg.set_value(self.outputs["status"], f"Error: Invalid JSON vector - {e}")
                return
                
            payload_str = self.get_input_value("payload") or "{}"
            try:
                payload = json.loads(payload_str)
                if not isinstance(payload, dict):
                    raise ValueError("Payload must be a dictionary")
            except json.JSONDecodeError as e:
                dpg.set_value(self.outputs["status"], f"Error: Invalid JSON payload - {e}")
                return
                
            try:
                collections = self.client.get_collections().collections
                collection_names = [c.name for c in collections]
            except:
                collection_names = []
                
            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                print(f"✅ Created collection: {collection_name}")
                
            point_id = str(uuid.uuid4())
            
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            
            dpg.set_value(self.outputs["status"], f"Success: Point added")
            dpg.set_value(self.outputs["point_id"], point_id)
            self.last_result = point_id
            print(f"✅ Point {point_id} added to {collection_name}")
            
        except Exception as e:
            error_text = f"Error: {str(e)}"
            dpg.set_value(self.outputs["status"], error_text)
            print(f"❌ Ошибка добавления точки: {e}")

    def process(self):
        print(f"QdrantAddNode {self.label} processing")
        return self.last_result

    def to_dict(self):
        """Сериализация состояния"""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "pos": dpg.get_item_pos(self.node_tag) if hasattr(self, 'node_tag') else self.pos,
            "collection_name": self.get_input_value("collection_name"),
            "vector_size": self.get_input_value("vector_size"),
            "mode": self.mode,
            "storage_path": self.storage_path,
            "last_result": self.last_result
        }

    @classmethod
    def from_dict(cls, data, parent="node_editor"):
        """Десериализация состояния — ИСПРАВЛЕНО"""
        node = cls(parent, data.get("pos", [100, 100]))
        
        if "collection_name" in data and "collection_name" in node.inputs:
            dpg.set_value(node.inputs["collection_name"], data["collection_name"])
        if "vector_size" in data and "vector_size" in node.inputs:
            dpg.set_value(node.inputs["vector_size"], data["vector_size"])
        if "mode" in data:  # ✅ ИСПРАВЛЕНО: было "if "mode" in"
            node.mode = data["mode"]
            if node.mode_combo:
                dpg.set_value(node.mode_combo, data["mode"])
        if "storage_path" in data:  # ✅ ИСПРАВЛЕНО: было "if "storage_path" in"
            node.storage_path = data["storage_path"]
            if node.storage_path_input:
                dpg.set_value(node.storage_path_input, data["storage_path"])
        
        node.update_mode(node.mode)
        
        try:
            if data.get("mode") == "In-Memory":
                node.client = QdrantClient(location=":memory:")
            else:
                storage_path = data.get("storage_path", "./qdrant_storage")
                node.client = QdrantClient(path=storage_path)
            node.is_connected = True
            print(f"✅ Auto-connected in {data.get('mode', 'In-Memory')} mode")
        except Exception as e:
            print(f"⚠️ Auto-connect failed: {e}")
            
        return node


class QdrantSearchNode(BaseNode):
    """Нода для поиска векторов в Qdrant в локальном режиме"""
    def __init__(self, parent="node_editor", pos=None):
        super().__init__("Qdrant Search", parent, pos)
        self.client = None
        self.is_connected = False
        self.last_results = []
        self.max_node_width = 350
        self.mode = "In-Memory"
        self.storage_path = "./qdrant_storage"
        self.storage_attr = None
        self.mode_combo = None
        self.storage_path_input = None

    def _create_inputs(self):
        # Режим работы Qdrant
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text("Qdrant Mode", wrap=300)
            self.mode_combo = dpg.add_combo(
                items=["In-Memory", "Local Storage"],
                default_value=self.mode,
                width=200,
                callback=lambda s, a, u=self: self.update_mode(a)
            )
            
        # Путь к локальному хранилищу
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static) as self.storage_attr:
            dpg.add_text("Storage Path:", wrap=300)
            self.storage_path_input = dpg.add_input_text(
                label="##storage_path",
                default_value=self.storage_path,
                width=min(200, self.max_node_width - 40)
            )
            dpg.add_button(
                label="Browse",
                callback=lambda s, a, u=self: self.browse_storage_path()
            )
            
        dpg.add_button(
            label="Connect",
            callback=lambda s, a, u=self: self.connect_to_qdrant()
        )
        dpg.add_separator()
        
        # Collection name
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_collection:
            dpg.add_text("Collection Name:", wrap=300)
            self.inputs["collection_name"] = dpg.add_input_text(
                label="##collection_search",
                default_value="documents",
                width=min(250, self.max_node_width - 40),
                wrap=True
            )
            self._register_attr(attr_id_collection, "input", "collection_name")
            
        # Query vector
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_query:
            dpg.add_text("Query Vector (JSON):", wrap=300)
            self.inputs["query_vector"] = dpg.add_input_text(
                label="##query_vector",
                multiline=True,
                height=60,
                width=min(250, self.max_node_width - 40),
                wrap=True,
                hint="[0.1, 0.2, 0.3, ...]"
            )
            self._register_attr(attr_id_query, "input", "query_vector")
            
        # Top K
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr_id_top_k:
            dpg.add_text("Top K:", wrap=300)
            self.inputs["top_k"] = dpg.add_input_int(
                label="##top_k",
                default_value=5,
                min_value=1,
                max_value=100,
                width=min(100, self.max_node_width - 40),
            )
            self._register_attr(attr_id_top_k, "input", "top_k")
            
        # Search button
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_button(label="Search", callback=lambda s, a, u=self: self.search())
            
        self.update_mode(self.mode)

    def _create_outputs(self):
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_results:
            dpg.add_text("Results:", wrap=300)
            self.outputs["results"] = dpg.add_input_text(
                label="##results",
                multiline=True,
                readonly=True,
                height=150,
                width=min(300, self.max_node_width - 40),
                wrap=True,
            )
            self._register_attr(attr_id_results, "output", "results")
            
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr_id_count:
            dpg.add_text("Count:", wrap=300)
            self.outputs["count"] = dpg.add_text("0", wrap=300)
            self._register_attr(attr_id_count, "output", "count")
            
        if hasattr(self, 'node_id') and self.node_id:
            dpg.set_item_width(self.node_id, self.max_node_width)

    def update_mode(self, mode):
        """Показывает/скрывает поле для пути к хранилищу"""
        self.mode = mode
        if self.storage_attr:
            if mode == "Local Storage":
                dpg.show_item(self.storage_attr)
            else:
                dpg.hide_item(self.storage_attr)

    def browse_storage_path(self):
        """Диалог выбора пути к хранилищу"""
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory()
        if path:
            dpg.set_value(self.storage_path_input, path)
            self.storage_path = path

    def connect_to_qdrant(self):
        """Подключение к Qdrant в локальном режиме"""
        try:
            mode = dpg.get_value(self.mode_combo)
            if mode == "In-Memory":
                self.client = QdrantClient(location=":memory:")
                status_text = "Connected to in-memory Qdrant"
                print(f"✅ {status_text}")
            else:
                self.storage_path = dpg.get_value(self.storage_path_input)
                self.client = QdrantClient(path=self.storage_path)
                status_text = f"Connected to local Qdrant at {self.storage_path}"
                print(f"✅ {status_text}")
                
            self.is_connected = True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            self.is_connected = False

    def search(self):
        """Поиск похожих векторов"""
        if not self.is_connected or not self.client:
            self.set_output_value("results", "Error: Not connected")
            return
            
        try:
            collection_name = self.get_input_value("collection_name") or "documents"
            top_k = self.get_input_value("top_k") or 5
            
            query_vector_str = self.get_input_value("query_vector")
            if not query_vector_str:
                self.set_output_value("results", "Error: Query vector is empty")
                return
                
            try:
                query_vector = json.loads(query_vector_str)
                if not isinstance(query_vector, list):
                    raise ValueError("Query vector must be a list")
            except json.JSONDecodeError as e:
                self.set_output_value("results", f"Error: Invalid JSON - {e}")
                return
                
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            
            results_text = ""
            for i, hit in enumerate(search_result, 1):
                results_text += f"--- Result {i} (Score: {hit.score:.4f}) ---\n"
                results_text += f"ID: {hit.id}\n"
                if hit.payload:
                    results_text += f"Payload: {json.dumps(hit.payload, indent=2, ensure_ascii=False)}\n"
                results_text += "\n"
                
            self.set_output_value("results", results_text)
            self.set_output_value("count", str(len(search_result)))
            self.last_results = search_result
            print(f"✅ Found {len(search_result)} results")
            
        except Exception as e:
            error_text = f"Error: {str(e)}"
            self.set_output_value("results", error_text)
            print(f"❌ Ошибка поиска: {e}")

    def process(self):
        print(f"QdrantSearchNode {self.label} processing")
        return self.last_results

    def to_dict(self):
        """Сериализация состояния"""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "pos": dpg.get_item_pos(self.node_tag) if hasattr(self, 'node_tag') else self.pos,
            "collection_name": self.get_input_value("collection_name"),
            "mode": self.mode,
            "storage_path": self.storage_path
        }

    @classmethod
    def from_dict(cls, data, parent="node_editor"):
        """Десериализация состояния — ИСПРАВЛЕНО"""
        node = cls(parent, data.get("pos", [100, 100]))
        
        if "collection_name" in data and "collection_name" in node.inputs:
            dpg.set_value(node.inputs["collection_name"], data["collection_name"])
        if "mode" in data:  # ✅ ИСПРАВЛЕНО
            node.mode = data["mode"]
            if node.mode_combo:
                dpg.set_value(node.mode_combo, data["mode"])
        if "storage_path" in data:  # ✅ ИСПРАВЛЕНО
            node.storage_path = data["storage_path"]
            if node.storage_path_input:
                dpg.set_value(node.storage_path_input, data["storage_path"])
        
        node.update_mode(node.mode)
        
        if data.get("mode") == "In-Memory":
            try:
                node.client = QdrantClient(location=":memory:")
                node.is_connected = True
                print(f"✅ Auto-connected in In-Memory mode")
            except Exception as e:
                print(f"⚠️ Auto-connect failed: {e}")
        else:
            try:
                storage_path = data.get("storage_path", "./qdrant_storage")
                node.client = QdrantClient(path=storage_path)
                node.is_connected = True
                print(f"✅ Auto-connected to {storage_path}")
            except Exception as e:
                print(f"⚠️ Auto-connect failed: {e}")
                
        return node