#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Cuddly, Duddly, and Fuddy, the Wuddlies - cozy/session.py
  Cozy session persistence for enjoying.
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""
import os
import json
from typing import List
from pathlib import Path

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import QPointF, QRectF, QSizeF

from cozy.warm import WarmNode  
from cozy.about import AboutNode
from cozy.graphics_view import GraphicsView

from app_info import APP_NAME

class SessionManager:
    """Gentle save/load for the entire sketchbook session — human-editable JSON"""
    @staticmethod
    def get_available_sessions(directory: str = "sessions") -> List[str]:
        path = Path(directory)
        
        files = [(f, f.stat().st_mtime) for f in path.glob("*.json") if f.is_file()]
        
        # Sort by mtime ascending → oldest first
        files.sort(key=lambda x: x[1])
        
        # Build nice display names
        names = [f.stem.replace("_", " ").title() for f, _ in files]
        
        return names

    @staticmethod
    def get_session_filename(display_name: str) -> str | None:
        return f"{display_name}.json"

    @staticmethod
    def refresh_combo(combo, current_name: str = None):
        sessions = SessionManager.get_available_sessions()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(sessions)

        if current_name and current_name in sessions:
            combo.setCurrentText(current_name)
        else:
            if APP_NAME in sessions:
                combo.setCurrentText(APP_NAME)
            elif sessions:
                combo.setCurrentText(sessions[0])
            else:
                combo.setCurrentText("Default Canvas")
        combo.blockSignals(False)

    # @staticmethod
    # def save_session(scene, filepath: str, view: QGraphicsView = None, 
    #                  progress_value: float = 100.0, joy_buckets: int = 0,
    #                  camera_pos: tuple = None, camera_zoom: float = None):
    #     """Save nodes information"""
    #     os.makedirs(os.path.dirname(filepath), exist_ok=True)
    #     nodes_data = []
    #     for item in scene.items():
    #         if isinstance(item, (WarmNode, AboutNode)):
    #             node_type = "about" if isinstance(item, AboutNode) else "warm"
    #             nodes_data.append({
    #                 "node_id": getattr(item, 'node_id', 0),
    #                 "type": node_type,
    #                 "title": item.title,
    #                 "full_text": item.full_text,
    #                 "pos_x": item.scenePos().x(),
    #                 "pos_y": item.scenePos().y(),
    #                 "width": item.rect().width(),
    #                 "height": item.rect().height()
    #             })
    #         data = {
    #         "version": "1.0",
    #         "nodes": nodes_data,
    #         "progress_value": round(progress_value, 2),
    #         "joy_buckets": int(joy_buckets)
    #     }

    #     # Handle Viewport Data
    #     if view is not None:
    #         if camera_pos and camera_zoom:
    #             scale = camera_zoom
    #             cx, cy = camera_pos
    #         else:
    #             transform = view.transform()
    #             scale = transform.m11()
    #             center = view.mapToScene(view.viewport().rect().center())
    #             cx, cy = center.x(), center.y()

    #         data["viewport"] = {
    #             "scale": round(scale, 4),
    #             "center_x": round(cx, 2),
    #             "center_y": round(cy, 2)
    #         }

    #     with open(filepath, "w", encoding="utf-8") as f:
    #         json.dump(data, f, indent=2, ensure_ascii=False)


    @staticmethod
    def save_session(scene, filepath: str, view: QGraphicsView = None, 
                     progress_value: float = 100.0, joy_buckets: int = 0,
                     camera_pos: tuple = None, camera_zoom: float = None):
        """Save nodes information with improved logic flow."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        nodes_data = []
        for item in scene.items():
            if isinstance(item, (WarmNode, AboutNode)):
                nodes_data.append({
                    "node_id": getattr(item, 'node_id', 0),
                    "type": "about" if isinstance(item, AboutNode) else "warm",
                    "title": item.title,
                    "full_text": item.full_text,
                    "pos_x": item.scenePos().x(),
                    "pos_y": item.scenePos().y(),
                    "width": item.rect().width(),
                    "height": item.rect().height()
                })
        data = {
            "version": "1.0",
            "nodes": nodes_data,
            "progress_value": round(progress_value, 2),
            "joy_buckets": int(joy_buckets)
        }

        # Viewport logic remains largely the same, but ensure it's outside the node loop
        if view is not None:
            if camera_pos and camera_zoom:
                scale = camera_zoom
                cx, cy = camera_pos
            else:
                transform = view.transform()
                scale = transform.m11()
                center = view.mapToScene(view.viewport().rect().center())
                cx, cy = center.x(), center.y()
            data["viewport"] = { "scale": round(scale, 4), "center_x": round(cx, 2), "center_y": round(cy, 2) }

        # Use a temporary file for "Atomic" saving
        temp_path = f"{filepath}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, filepath)

    @staticmethod
    def load_session(scene, filepath: str, view: QGraphicsView = None):
        """Load nodes with registry-based mapping and error protection."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️ Cozy Alert: Could not read session file {filepath}: {e}")
            return None

        # 1. Clear old nodes
        # We target our specific node classes to avoid nuking UI elements
        for item in list(scene.items()):
            if isinstance(item, (WarmNode, AboutNode)):
                scene.removeItem(item)

        # 2. Define Registry (This makes adding Render/Image nodes easy!)
        NODE_TYPE_MAP = {
            "warm": WarmNode,
            "about": AboutNode,
            # "render": RenderNode, # Future proofing!
            # "image": ImageNode,
        }

        # 3. Restore nodes
        for node_data in data.get("nodes", []):
            try:
                node_type_str = node_data.get("type", "warm")
                node_class = NODE_TYPE_MAP.get(node_type_str, WarmNode) # Default to Warm

                # Standard instantiation - assumes they share a common signature
                node = node_class(
                    node_id=node_data.get("node_id", 0),
                    title=node_data.get("title", ""),
                    full_text=node_data.get("full_text", ""),
                    pos=QPointF(node_data.get("pos_x", 0), node_data.get("pos_y", 0))
                )

                # Apply geometry
                width = node_data.get("width", node.rect().width())
                height = node_data.get("height", node.rect().height())
                node.prepareGeometryChange()
                node.setRect(QRectF(node.rect().topLeft(), QSizeF(width, height)))
                
                scene.addItem(node)
            except KeyError as e:
                print(f"❌ Skipping a node due to missing field: {e}")
                continue

        scene.setSceneRect(scene.itemsBoundingRect())

        # 4. Restore viewport
        if view is not None and "viewport" in data:
            vp = data["viewport"]
            view.resetTransform()
            view.scale(vp.get("scale", 1.0), vp.get("scale", 1.0))
            view.centerOn(QPointF(vp.get("center_x", 0.0), vp.get("center_y", 0.0)))
            view.viewport().update()

        return data
