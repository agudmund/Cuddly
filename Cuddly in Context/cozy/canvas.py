#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# cozy/canvas.py
# Cozy canvas panel for enjoying — now part of the global Cozy toolkit 🌱
# Built using a single shared braincell by Yours Truly and Grok (February 2026)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QBrush, QPixmap, QPainter, QPen
import random
from math import radians, cos, sin
from cozy.graphics_view import GraphicsView
from cozy.warm import WarmNode

class CozyCanvas:
    """Full utility class for the Paradisic Fields canvas panel 🌱"""

    @staticmethod
    def node() -> WarmNode:
        """Tiny cozy factory — makes adding starter nodes delightful and reusable 🌱"""
        return WarmNode(
            node_id=1,
            full_text=" and that.",
            pos=QPointF(0, 0)
        )

    @staticmethod
    def create_canvas_panel(parent):
        """
        Creates and returns the full interactive canvas panel.
        Returns: (QWidget, GraphicsView, QGraphicsScene)
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Scene + View
        scene = QGraphicsScene()
        scene.setBackgroundBrush(QColor("#1e1e1e"))
        view = GraphicsView(scene, parent)
        view.setMinimumWidth(600)
        view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(view)

        # Starter content: welcome node
        welcome = CozyCanvas.node()
        scene.addItem(welcome)
        view.centerOn(0, 0)

        return panel, view, scene