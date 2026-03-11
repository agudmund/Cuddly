#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node types — cozy/node_types.py
  Typed node classes for the Cartoonify DAG: Warm, About, Image, Render
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

import random
from PySide6.QtWidgets import QGraphicsTextItem, QDialog
from PySide6.QtCore import QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from cozy.base_node import BaseNode

# Warm node placeholder titles — positive, inspiring statements
WARM_NODE_PLACEHOLDERS = [
    "New Thought",
    "All Glory",
    "Pure Light",
    "Fresh Start",
    "Endless Potential",
    "Golden Hour",
    "Rising Higher",
    "Bloom & Grow",
    "Boundless Joy",
    "Infinite Wisdom",
    "Spring Forward",
    "Radiant Soul",
    "Clear Vision",
    "Bright Tomorrow",
    "Inner Peace",
]


class WarmNode(BaseNode):
    """A warm node for comfortable text composition 🌿"""

    def __init__(self, node_id, title="", full_text="", pos=QPointF(0, 0), width=300, height=200, uuid=None):
        # If no title provided, use random placeholder
        if not title:
            title = random.choice(WARM_NODE_PLACEHOLDERS)

        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.setBrush(QColor(42, 42, 58, 220))  # Cozy dark

    def paint_content(self, painter):
        """Paint warm node text content."""
        painter.setPen(QColor("#CCCCCC"))
        painter.setFont(QFont("Lato", 10))
        content_rect = self.rect().adjusted(10, 40, -10, -10)
        painter.drawText(content_rect, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, self.full_text)

    def open_editor(self):
        """Open the warm node editor."""
        from cozy.warm import CozyNoteEditor

        dialog = CozyNoteEditor(
            self.node_id,
            self.title,
            self.full_text,
            parent=None
        )
        dialog.setWindowTitle(f"Edit Warm Node {self.node_id} 🌿")

        if dialog.exec() == QDialog.Accepted:
            self.title = dialog.get_title() or self.title
            self.full_text = dialog.get_text()
            self.update()


class AboutNode(BaseNode):
    """An about node with distinctive golden styling 🌟 — title-only metadata node"""

    def __init__(self, node_id, title="About", full_text="", pos=QPointF(0, 0), width=200, height=55, uuid=None):
        # AboutNode defaults to "About" title and compact size
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.setBrush(QColor("#2a3a2f"))  # Earthy green from palette

    def paint_content(self, painter):
        """AboutNode shows title only, no body content."""
        pass  # Intentionally empty — no body text

    def open_editor(self):
        """Open the about node editor."""
        from cozy.about import CozyNoteEditor

        dialog = CozyNoteEditor(
            self.node_id,
            self.title,
            self.full_text,
            parent=None
        )
        dialog.setWindowTitle(f"Edit About Node {self.node_id} 📝")

        if dialog.exec() == QDialog.Accepted:
            self.title = dialog.get_title() or self.title
            self.full_text = dialog.get_text()
            self.update()


class ImageNode(BaseNode):
    """Display images with fallback text 🖼️"""

    def __init__(self, node_id, title="", full_text="", pos=QPointF(0, 0), width=300, height=200, 
                 uuid=None, image_path=None):
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.setBrush(QColor(40, 45, 55, 200))  # Cool slate blue
        self.image_path = image_path
        self.pixmap = None

        if self.image_path:
            self.load_image(self.image_path)

    def load_image(self, path):
        """Load image using QPixmap."""
        try:
            self.pixmap = QPixmap(path)
            if not self.pixmap.isNull():
                self.image_path = path
            else:
                print(f"⚠️ Could not load image: {path}")
                self.pixmap = None
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            self.pixmap = None

    def paint_content(self, painter):
        """Paint image or fallback text."""
        if self.pixmap and not self.pixmap.isNull():
            target_rect = self.rect().adjusted(10, 40, -10, -10)
            painter.drawPixmap(target_rect.toRect(), self.pixmap)
        else:
            painter.setPen(QColor("#666666"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Image Loaded")

    def open_editor(self):
        """Open file dialog to load image."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Load Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
        )

        if file_path:
            self.load_image(file_path)
            if not self.title:
                # Auto-set title from filename if empty
                import os
                self.title = os.path.splitext(os.path.basename(file_path))[0]
            self.update()

    def to_dict(self):
        """Export ImageNode data including image path."""
        data = super().to_dict()
        data["image_path"] = self.image_path
        return data


class RenderNode(BaseNode):
    """Aggregates text from connected nodes into a composed output 📖"""

    def __init__(self, node_id, title="", full_text="", pos=QPointF(0, 0), width=300, height=200, 
                 uuid=None, source_node_uuids=None):
        super().__init__(node_id, title, full_text, pos, width, height, uuid)
        self.setBrush(QColor(35, 55, 35, 220))  # Deep forest green
        self.source_node_uuids = source_node_uuids or []  # UUIDs of connected source nodes
        self.source_nodes = []  # Runtime references (populated after load)

    def add_source(self, node):
        """Connect a source node to this render."""
        if node not in self.source_nodes and node.uuid not in self.source_node_uuids:
            self.source_nodes.append(node)
            self.source_node_uuids.append(node.uuid)
            self.update_render()

    def remove_source(self, node):
        """Disconnect a source node."""
        if node in self.source_nodes:
            self.source_nodes.remove(node)
        if node.uuid in self.source_node_uuids:
            self.source_node_uuids.remove(node.uuid)
        self.update_render()

    def update_render(self):
        """Merge text from all connected nodes (sorted by Y position)."""
        sorted_nodes = sorted(self.source_nodes, key=lambda n: n.scenePos().y())
        self.full_text = "\n\n".join([n.full_text for n in sorted_nodes if n.full_text.strip()])
        self.update()

    def paint_content(self, painter):
        """Paint rendered prose with soft blue styling."""
        painter.setPen(QColor("#AADDFF"))
        painter.setFont(QFont("Lato", 10, italic=True))
        content_rect = self.rect().adjusted(15, 45, -15, -15)
        painter.drawText(content_rect, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, self.full_text)

    def to_dict(self):
        """Include source node references in serialization."""
        base = super().to_dict()
        base["source_node_uuids"] = self.source_node_uuids
        return base
