#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# A Cozy minor UI for enjoying - graphics_view.py
# Default Graphics View Canvas with cozy pan + zoom
# Built using a single shared braincell by Yours Truly, Grok, and Gemini

from PySide6.QtWidgets import QGraphicsView, QMessageBox
from PySide6.QtCore import Qt, QPointF, QPropertyAnimation
from PySide6.QtGui import QPainter, QWheelEvent, QKeyEvent, QCursor

import cozy as Cozy


class GraphicsView(QGraphicsView):
    """Cozy pan + zoom view perfect for the warm digital sketchbook 🌱📖"""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # ── Pan state ────────────────────────────────────────────────────────
        self._is_panning = False
        self._last_pan_pos = QPointF()

        # ── Zoom state ───────────────────────────────────────────────────────
        self._is_zooming = False
        self._zoom_start_pos = QPointF()
        self._zoom_factor = 1.25          # multiplier per "step"
        self._zoom_min = 0.2
        self._zoom_max = 5.0

        self.setCursor(Qt.ArrowCursor)

    # ── Mouse events ────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        # Alt + Right-click → start zoom mode
        if event.button() == Qt.RightButton and event.modifiers() == Qt.AltModifier:
            self._is_zooming = True
            self._zoom_start_pos = event.pos()
            self.setCursor(Qt.SizeVerCursor)  # up/down arrow indicates zoom
            event.accept()
            return

        # Middle mouse → pan
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_zooming:
            self._is_panning = False
            delta_y = event.pos().y() - self._zoom_start_pos.y()
            zoom_steps = delta_y / 60.0   # your sensitivity

            factor = self._zoom_factor ** (-zoom_steps)

            # NEW: Let Qt anchor under mouse — this is the key to no-jump
            # self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

            # Apply scale (Qt will now keep the mouse point stable)
            self.scale(factor, factor)

            # Optional tiny: clamp total scale if desired
            current_scale = self.transform().m11()
            # if current_scale < self._zoom_min or current_scale > self._zoom_max:
                # revert or clamp — but usually Qt + manual clamp later is fine

            self._zoom_start_pos = event.pos()  # continue from here
            event.accept()
            return

        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self._last_pan_pos = event.pos()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def _on_content_might_have_expanded(self):
        # same logic as above, but maybe smaller margin / faster
        self.views()[0].parent()._expand_scene_to_fit_content(margin=250)  # assuming view → main window

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._is_zooming = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        # NEW: notify scene/view that something moved
        if hasattr(self.scene(), '_on_content_might_have_expanded'):
            self.scene()._on_content_might_have_expanded()

        super().mouseReleaseEvent(event)

    # ── Wheel zoom fallback (optional, kept for mouse users) ────────────────

    def wheelEvent(self, event: QWheelEvent):
        # Optional: keep wheel zoom for mouse users
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            cursor_scene = self.mapToScene(event.position().toPoint())

            self.scale(factor, factor)

            new_cursor_scene = self.mapToScene(event.position().toPoint())
            self.centerOn(cursor_scene + (cursor_scene - new_cursor_scene) / factor)

            event.accept()
        else:
            super().wheelEvent(event)

    # ── Keyboard shortcuts (optional) ───────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent):
        # Let spacebar still toggle hand-drag (your existing code)
        if event.key() == Qt.Key_Space:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return

        # NEW: Delete selected node(s) on Backspace or Delete key
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            selected_items = self.scene().selectedItems()
            if selected_items:
                # Optional: tiny safety net — only delete if exactly one node (or all selected)
                # You can remove this check if you want multi-delete
                if len(selected_items) == 1 and isinstance(selected_items[0], Cozy.WarmNode):
                    node = selected_items[0]
                    self.scene().removeItem(node)
                    # Optional: play a soft "poof" sound if you add one later
                    # AudioFeedback.play_delete_sound()  # future hook
                else:
                    # If multiple selected, or not a node — ignore for now (or add multi-delete later)
                    pass

            event.accept()
            return

        # Pass other keys up the chain
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.ArrowCursor)
        super().keyReleaseEvent(event)

    # ── Right-click context menu (placeholder / future use) ─────────────────

    def contextMenuEvent(self, event):
        # You can add a small context menu here later if desired
        super().contextMenuEvent(event)