#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Cuddly, Duddly, and Fuddy, the Wuddlies - cozy/about.py
  The cozy about node class for enjoying
  Built using a single shared braincell by Yours Truly, Grok, And Gemini (February 2026)
"""

import re
import random
import textwrap
from PySide6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsItem,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QDialogButtonBox,
    QLabel,
    QGraphicsDropShadowEffect,
    QGraphicsPixmapItem,
    QGraphicsItemGroup,
    QLineEdit,
    QFormLayout,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QDialog,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QGraphicsView,
    QStackedWidget,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsPixmapItem,
    QGraphicsEllipseItem,
    QGraphicsSimpleTextItem,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, QSizeF, QObject
from PySide6.QtGui import (
    QColor, QBrush, QPen, QFont, QPixmap, QPainter, QPainterPath,QFontMetrics
)

import textwrap
from cozy import nodal

class CozyNoteEditor(QDialog):
    """Much larger, cozy note editor with dedicated title field 🌱📝"""
    def __init__(self, node_id: int, current_title: str, current_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Note {node_id} 🌿")
        self.setMinimumSize(940, 680)
        self.resize(980, 740)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        header = QLabel(f"Editing Note {node_id} 🌱")
        layout.addWidget(header)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        self.title_edit = QLineEdit(current_title)
        self.title_edit.setPlaceholderText("Give this note a gentle name…")
        form_layout.addRow("Title:", self.title_edit)
        layout.addLayout(form_layout)

        self.text_edit = QTextEdit(current_text)
        layout.addWidget(self.text_edit)

        # In the dialog's __init__ (after creating the layout)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 12, 0, 0)
        button_layout.setSpacing(12)

        save_btn = nodal.button("Save Note 🌿", clicked=self.accept)

        # Optional: make Save more prominent
        save_btn.setDefault(True)
        save_btn.setStyleSheet(save_btn.styleSheet() + "font-weight: bold;")

        button_layout.addStretch()
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)  # add to your existing layout

    def get_title(self): return self.title_edit.text().strip()
    def get_text(self):  return self.text_edit.toPlainText().strip()

class Port(QGraphicsEllipseItem):
    def __init__(self, parent_node, is_output=False):
        super().__init__(-10, -10, 20, 20, parent_node)
        
        base_color = QColor(180, 140, 120) if not is_output else QColor(140, 190, 160)
        self.setBrush(QBrush(base_color.lighter(115)))
        self.setPen(QPen(QColor(60, 60, 80, 100), 1))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)
        self.edge = None

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(12)
        glow.setColor(base_color.darker(140))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

class AboutNode(QGraphicsRectItem, QObject):
    """A single warm, draggable, editable text node with title 🌿📝"""

    # Configurable cozy constants
    BASE_WIDTH       = 200
    MIN_HEIGHT       = 50
    MAX_HEIGHT       = 50      # prevent runaway growth
    TEXT_WIDTH       = 200      # matches setTextWidth
    PADDING_TOP      = 45       # space for title + emoji
    PADDING_BOTTOM   = 20
    LINE_HEIGHT      = 22       # approximate line height at font 13.5

    def __init__(self, node_id: int, title: str = "", full_text: str = "", pos: QPointF = QPointF(0, 0)):
        super().__init__(QRectF(-145, -68, self.BASE_WIDTH, self.MIN_HEIGHT))
        self.node_id = node_id
        self.full_text = full_text.strip()
        self.title = "About"
        self.setPos(pos)

        self._resize_handle_size = 12
        self._is_resizing = False

        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(self.rect().center())

        self.setBrush(QBrush(QColor("#2a2a3a")))
        self.setPen(QPen(QColor("#6b5a47"), 1))
        self.round_radius = 18

        # Title display (always trimmed for the node)
        self.title_item = QGraphicsTextItem("About", self)
        self.title_item.setFont(QFont("Chandler42", 15))
        self.title_item.setDefaultTextColor(QColor("#e8f0ff"))
        self.title_item.setPos(-135, -65)
        self.title_item.setTextWidth(-1)

        # Body text with wrapping
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont("Lato", 13.5))
        self.text_item.setDefaultTextColor(QColor("#ffffff"))
        self.text_item.setPos(-85, -35)

        self.thumbnail_group = None

        # Final size adjustment after all items are added
        self._adjust_node_height()
        self._refresh_body_wrap()

    def show_about(self):  
        """Open About using the cozy centralized helper"""  
        from dialogs.about_dialog import AboutDialog
        parent = self.scene().views()[0] if self.scene() and self.scene().views() else None  
        nodal.cozy_dialog(AboutDialog, parent)  

    def _refresh_body_wrap(self):
        """Update body text wrap width to match current node size."""
        if not self.full_text:
            self.text_item.setPlainText("")
            return
        
        # Responsive wrap: node width minus generous left/right padding
        wrap_width = self.rect().width() - 60  # adjust 60 to taste (30px each side)
        self.text_item.setTextWidth(max(100, wrap_width))  # min 100 to avoid collapse
        
        # Re-set the text so it re-wraps immediately
        self.text_item.setPlainText(self.full_text)

    def _update_preview_text(self):
        wrapped = textwrap.fill(self.full_text, width=38)
        self.text_item.setPlainText(wrapped)
        self._adjust_node_height()              # resize whenever text changes

    def _adjust_node_height(self):
        """Calculate needed height from text content + padding"""
        
        final_height = max(self.MIN_HEIGHT, self.MAX_HEIGHT, self.MIN_HEIGHT)

        # Update rect (keep top-left anchored, grow downward)
        current_rect = self.rect()
        self.setRect(QRectF(current_rect.left(), current_rect.top(),
                            self.BASE_WIDTH, final_height))

        # Keep transform origin centered so scaling/position feels natural
        self.setTransformOriginPoint(self.rect().center())

    def paint(self, painter: QPainter, option, widget=None):
        # painter.setBrush(QBrush(QColor("#2a2a3a")))
        painter.setBrush(QBrush(QColor("#2a3a2f")))
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), self.round_radius, self.round_radius)

    def shape(self):
        """Define the exact rounded rectangle shape for clipping and collision."""
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.round_radius, self.round_radius)
        return path

    def _update_preview_text(self):
        """Word-wrapped body text"""
        wrapped = textwrap.fill(self.full_text, width=38)   # 38 chars ≈ 200px at this font size
        self.text_item.setPlainText(wrapped)

    def mouseDoubleClickEvent(self, event):  
        if event.button() == Qt.LeftButton:  
            title_area = QRectF(-135, -65, 180, 30)  # Adjust to your title bounds  
            if not title_area.contains(event.pos()):  # Only open if not on title  
                self.show_about()  
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if not self._is_resizing:
            return super().mouseMoveEvent(event)

        delta = event.pos() - self._resize_start_pos
        new_width = max(120, self._resize_start_rect.width() + delta.x())
        new_height = max(100, self._resize_start_rect.height() + delta.y())

        if event.modifiers() & Qt.ShiftModifier:
            orig_ratio = self._resize_start_rect.width() / self._resize_start_rect.height()
            new_height = new_width / orig_ratio

        self.prepareGeometryChange()
        self.setRect(QRectF(self.rect().topLeft(), QSizeF(new_width, new_height)))
        self._update_preview_text()  # lightweight, so keep immediate
        self._refresh_body_wrap()  # run immediately on first move

        event.accept()

    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setScale(1.085)
        self.setPen(QPen(self.pen().color().lighter(135), 1))

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.setScale(1.0)
        self.setPen(QPen(QColor("#6b5a47"), 1))
