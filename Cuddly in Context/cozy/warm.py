#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Jacket - cozy/warm.py
  A warm node for enjoying.
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

import re
import random
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QLineEdit, QFormLayout, QGraphicsTextItem, 
    QGraphicsObject, QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QPointF, QRectF, QTimer, QSizeF, QVariantAnimation, QPropertyAnimation,
    QEasingCurve, Property
)
from PySide6.QtGui import (
    QColor, QBrush, QPen, QFont, QPainter, QPainterPath, QFontMetrics, QTextDocument
)

from cozy import nodal 
from utils.spellchecker import SpellHighlighter, show_spell_suggestions

class CozyNoteEditor(QDialog):
    """Larger, cozy note editor with dedicated title field, spellchecking & gentle joy 🌱📝"""

    def __init__(self, node_id: int, current_title: str, current_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Note {node_id} 🌿")
        self.setMinimumSize(940, 680)

        # Track original state for unsaved changes glow
        self.current_text = current_text
        self.original_title = current_title.strip()
        self.original_text = current_text.strip()
        self.has_unsaved_changes = False

        # === Warm cozy styling ===
        self.setStyleSheet("""
            QLineEdit, QTextEdit {
                background: #363646;
                color: #ffffff;
                border: 1px solid #6b5a47;
                border-radius: 12px;
                padding: 12px;
                font-family: 'Lato';
                selection-color: #ffffff;
                selection-background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2e2e2e, stop:0.4 #5c3e4f,
                    stop:0.7 #a56a85, stop:1 #d87a9e
                );
            }
            QLabel {
                color: #a8d0ff;
                font-family: 'Chandler42';
            }
            QPushButton {
                background: #4a3a3f;
                color: #ffb6c1;
                border: none;
                border-radius: 12px;
                padding: 10px 16px;
                font-family: 'Chandler42';
                font-size: 14px;
            }
            QPushButton:hover {
                background: #6a4a5f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(18)

        # Title row
        title_row = QHBoxLayout()
        self.title_edit = QLineEdit(current_title)
        self.title_edit.setPlaceholderText("Give this note a gentle name…")
        self.title_edit.setFont(QFont("Chandler42", 16))
        self.title_edit.setMinimumHeight(50)

        emoji_btn = nodal.button("🌸", fixedWidth=42)
        emoji_btn.clicked.connect(self._insert_random_emoji)

        title_row.addWidget(self.title_edit, 1)
        title_row.addWidget(emoji_btn)
        layout.addLayout(title_row)

        # === Main text area — now with live Markdown rendering! ===
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(current_text)
        self.text_edit.setFont(QFont("Lato", 13))
        self.text_edit.setMinimumHeight(420)
        layout.addWidget(self.text_edit)

        # Spellchecking still works beautifully
        self.highlighter = SpellHighlighter(self.text_edit.document())
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(
            lambda pos: show_spell_suggestions(self.text_edit, pos)
        )

        # Word count (with happy heartbeat pop!)
        self.word_count = QLabel("0 gentle words 💛")
        self.word_count.setAlignment(Qt.AlignRight)
        self.word_count.setStyleSheet("color: #a8d0ff; font-size: 13px;")
        layout.addWidget(self.word_count)

        # Save button with gentle breathing glow when dirty
        button_layout = QHBoxLayout()
        self.save_btn = nodal.button("Save Note 🌿", clicked=self.accept)
        self.save_btn.setDefault(True)
        self.save_btn.setMinimumHeight(48)

        # Pulse animation (reused)
        self.pulse_anim = QVariantAnimation(self)
        self.pulse_anim.setDuration(2200)
        self.pulse_anim.setStartValue(8)
        self.pulse_anim.setEndValue(26)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pulse_anim.setLoopCount(-1)

        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        # Connections
        self.text_edit.textChanged.connect(self._on_content_changed)
        self.title_edit.textChanged.connect(self._on_content_changed)
        self.last_word_count = 0
        self._update_word_count()

    def _create_glow_effect(self):
        """Fresh glow every time we need it (avoids deleted object errors)"""
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(12)
        effect.setColor(QColor("#ff9ab5"))
        effect.setOffset(0, 0)
        self.pulse_anim.valueChanged.connect(effect.setBlurRadius)  # connect to new effect
        return effect

    def _on_content_changed(self):
        """Detect unsaved changes and show/hide glow only when needed"""
        has_changes = (self.title_edit.text().strip() != self.original_title or 
                       self.text_edit.toPlainText().strip() != self.original_text)

        if has_changes != self.has_unsaved_changes:
            self.has_unsaved_changes = has_changes
            
            if has_changes:
                self.save_btn.setText("Save Changes 🌿")
                self.save_btn.setGraphicsEffect(self._create_glow_effect())
                if self.pulse_anim.state() != QVariantAnimation.Running:
                    self.pulse_anim.start()
            else:
                self.save_btn.setText("Save Note 🌿")
                self.save_btn.setGraphicsEffect(None)
                if self.pulse_anim.state() == QVariantAnimation.Running:
                    self.pulse_anim.stop()

        self._update_word_count()

    def mark_as_saved(self):
        """Called after successful save so the button goes calm again"""
        self.original_title = self.title_edit.text().strip()
        self.original_text = self.text_edit.toPlainText().strip()
        self.has_unsaved_changes = False
        self.save_btn.setText("Save Note 🌿")
        self.save_btn.setGraphicsEffect(None)
        if self.pulse_anim.state() == QVariantAnimation.Running:
            self.pulse_anim.stop()

    def _update_word_count(self):
        words = len(self.text_edit.toPlainText().split())
        self.word_count.setText(f"{words} gentle words 💛")

        if words > self.last_word_count:
            self._happy_word_heartbeat()
        self.last_word_count = words

    def _happy_word_heartbeat(self):
        """Joyful little pop when word count increases"""
        anim = QVariantAnimation(self)
        anim.setDuration(160)
        anim.setStartValue(13)
        anim.setEndValue(15.8)
        anim.setEasingCurve(QEasingCurve.OutBack)

        def return_to_normal():
            back = QVariantAnimation(self)
            back.setDuration(240)
            back.setStartValue(15.8)
            back.setEndValue(13)
            back.setEasingCurve(QEasingCurve.OutQuad)
            back.valueChanged.connect(lambda s: self.word_count.setStyleSheet(
                f"color: #a8d0ff; font-family: 'Chandler42'; font-size: {s}px;"
            ))
            back.start()

        anim.valueChanged.connect(lambda s: self.word_count.setStyleSheet(
            f"color: #ff9ab5; font-family: 'Chandler42'; font-size: {s}px;"
        ))
        anim.finished.connect(return_to_normal)
        anim.start()

    def _insert_random_emoji(self):
        """Sprinkle a little joy into the world ✨"""
        emojis = ["🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"]
        self.text_edit.insertPlainText(random.choice(emojis) + " ")

    def get_title(self):
        return self.title_edit.text().strip()

    def get_text(self):
        # Use toPlainText() to keep \n characters intact
        return self.text_edit.toPlainText()

class WarmNode(QGraphicsObject):
    """A refactored, performance-optimized cozy node with a centered pulse 🌿"""
    
    MIN_WIDTH = 180
    MIN_HEIGHT = 60
    MAX_HEIGHT = 1000
    MARGIN = 20
    TITLE_Y_OFFSET = 5

    def __init__(self, node_id: int, title: str = "", full_text: str = "", pos: QPointF = QPointF(0, 0)):
        super().__init__()
        
        self.node_id = node_id
        self.title = title.strip() or self._generate_fallback_title()
        self.full_text = full_text
        
        # Internal geometry storage
        self._rect = QRectF(0, 0, 250, 150)
        self.setPos(pos)
        
        # FIXED: Set origin to center for balanced scaling
        self.setTransformOriginPoint(self._rect.center())
        
        self.setFlags(self.GraphicsItemFlag.ItemIsMovable | 
                      self.GraphicsItemFlag.ItemIsSelectable | 
                      self.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # --- Inside WarmNode.__init__ ---
        self.pulse_anim = QVariantAnimation(self)
        self.pulse_anim.setDuration(350)    # <--- CHANGE THIS FOR SPEED (ms)
        self.pulse_anim.setStartValue(1.0)
        self.pulse_anim.setEndValue(1.020)  # <--- CHANGE THIS FOR SIZE (1.0 = 100%)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutQuad) 
        self.pulse_anim.valueChanged.connect(self.setScale)

        # Styling
        self.brush = QBrush(QColor("#2a2a3a"))
        self.base_pen = QPen(QColor("#6b5a47"), 1)
        self.hover_pen = QPen(QColor("#6b5a47").lighter(135), 1)
        self.current_pen = self.base_pen
        self.round_radius = 18

        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._sync_content_layout)

        # Iconic Items
        self.emoji_item = QGraphicsTextItem(random.choice(["🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌","💖"]), self)
        self.emoji_item.setFont(QFont("Segoe UI Emoji", 24))

        # The Node Title
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setFont(QFont("Chandler42", 20, QFont.Bold))
        self.title_item.setDefaultTextColor(QColor("#a8d0ff"))

        # The Node Body Text
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setFont(QFont("Lato", 12))
        self.text_item.setDefaultTextColor(QColor("#ffffff"))
        
        self._is_resizing = False
        self._sync_content_layout()

    # --- API COMPATIBILITY ---

    def rect(self):
        """Returns the current rectangle, fixing session load errors."""
        return self._rect

    def setRect(self, rect):
        """Standard setter that ensures the transform origin stays centered."""
        self.prepareGeometryChange()
        self._rect = rect
        self.setTransformOriginPoint(self._rect.center())
        self._sync_content_layout()
        self.update()

    def boundingRect(self):
        return self._rect

    # Property fix for QPropertyAnimation console warnings
    def get_graphics_effect(self): return self.graphicsEffect()
    def set_graphics_effect(self, effect): self.setGraphicsEffect(effect)
    graphicsEffect_prop = Property(object, get_graphics_effect, set_graphics_effect)

    # --- CORE LOGIC ---

    def _generate_fallback_title(self):
        # if self.full_text:
        #     first_line = re.split(r'[.!?]\s*|\n', self.full_text, maxsplit=1)[0].strip()
        #     return (first_line[:30] + "…") if len(first_line) > 30 else first_line
        return random.choice(["New Thought", "All Glory"])

    def _sync_content_layout(self):
        r = self._rect
        self.setTransformOriginPoint(r.center())

        # === Always keep emoji + title visible and nicely placed ===
        self.emoji_item.setPos(r.left() + 12, r.top() + 8)

        metrics = QFontMetrics(self.title_item.font())
        elided_title = metrics.elidedText(self.title, Qt.ElideRight, r.width() - 80)
        self.title_item.setPlainText(elided_title)
        self.title_item.setPos(r.left() + 55, r.top() + 9)
        
        # === Tiny title-card mode (sleek 60 px cards) ===
        if r.height() < 95:
            self.text_item.setVisible(False)           # ← this is the key!
        else:
            # Normal mode with body text
            self.text_item.setVisible(True)

            doc = QTextDocument()
            doc.setDefaultFont(self.text_item.font())
            doc.setPlainText(self.full_text)
            doc.setTextWidth(r.width() - (self.MARGIN * 2))
            
            self.text_item.setDocument(doc)
            self.text_item.setPos(r.left() + self.MARGIN, r.top() + 55)

            # Only auto-grow if text actually needs more space
            content_needed = doc.size().height() + 85
            if content_needed > r.height() + 8:
                final_h = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, content_needed))
                if abs(r.height() - final_h) > 4:
                    self.prepareGeometryChange()
                    self._rect.setHeight(final_h)
                    self.setTransformOriginPoint(self._rect.center())

        self.update()

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush)
        
        if self.isSelected():
            painter.setPen(QPen(self.base_pen.color().lighter(150), 2))
        else:
            painter.setPen(self.current_pen)
            
        painter.drawRoundedRect(self._rect, self.round_radius, self.round_radius)

        # Resize grip
        painter.setPen(QPen(QColor(255, 255, 255, 40), 2))
        br = self._rect.bottomRight()
        for i in range(3):
            offset = (i + 1) * 5
            painter.drawLine(br.x() - offset, br.y() - 2, br.x() - 2, br.y() - offset)

    def mousePressEvent(self, event):
        handle_rect = QRectF(self._rect.right()-25, self._rect.bottom()-25, 25, 25)
        if handle_rect.contains(event.pos()):
            self._is_resizing = True
            self._resize_start_pos = event.scenePos()
            self._resize_start_rect = QRectF(self._rect)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            delta = event.scenePos() - self._resize_start_pos
            new_w = max(self.MIN_WIDTH, self._resize_start_rect.width() + delta.x())
            new_h = max(self.MIN_HEIGHT, self._resize_start_rect.height() + delta.y())
            
            # Use the fixed setRect to maintain center origin during drag
            self.setRect(QRectF(self._rect.topLeft(), QSizeF(new_w, new_h)))
            
            if not self._resize_timer.isActive():
                self._resize_timer.start(30)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_resizing = False
        self._sync_content_layout()
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        # Update border color immediately
        self.current_pen = self.hover_pen
        self.update()

        # Gentle one-shot pulse (up AND down) — no more warnings or errors
        if self.pulse_anim.state() == QVariantAnimation.Stopped:
            self.pulse_anim.setDirection(QVariantAnimation.Forward)
            self.pulse_anim.start()

            def reverse_pulse():
                if self.pulse_anim.direction() == QVariantAnimation.Forward:
                    self.pulse_anim.setDirection(QVariantAnimation.Backward)
                    self.pulse_anim.start()

            # PySide6-safe disconnect (this is the line that fixes everything)
            if self.pulse_anim.receivers("finished") > 0:
                self.pulse_anim.finished.disconnect()

            self.pulse_anim.finished.connect(reverse_pulse)

        super().hoverEnterEvent(event)

    def _on_editor_accepted(self):
        """User clicked Save → apply changes"""
        if hasattr(self, '_editor') and self._editor:
            self.title = self._editor.get_title()
            self.full_text = self._editor.get_text() 
            self._sync_content_layout()
            self.update()
            self._editor.mark_as_saved()
            self.scene().update()  # refresh node appearance
            del self._editor  # clean up reference

    def _on_editor_rejected(self):
        """User clicked Cancel / closed window → do nothing"""
        if hasattr(self, '_editor') and self._editor:
            del self._editor  # just clean up

    def hoverLeaveEvent(self, event):
        # Restore the border color, but do NOT touch the scale
        self.current_pen = self.base_pen
        self.update()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Create the editor (still parented so it centers nicely and stays on top of our window)
        self._editor = CozyNoteEditor(self.node_id, self.title, self.full_text, parent=self.scene().views()[0].window())
        # self._editor.setWindowFlags(self._editor.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Connect signals so we know when the user saves or closes
        self._editor.accepted.connect(self._on_editor_accepted)
        self._editor.rejected.connect(self._on_editor_rejected)
        
        # Show non-blocking (this returns immediately → main UI stays alive!)
        self._editor.setModal(False)
        self._editor.show()
        
        super().mouseDoubleClickEvent(event)