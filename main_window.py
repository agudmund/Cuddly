#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Cuddly, Duddly, and Fuddy, the Wuddlies - main_window.py
  FULL RESTORATION: Bringing the 'Glory' back to the 'Stable' foundation.
"""

import os
import random
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QPoint, QPointF, QRectF, QSize
)
from PySide6.QtGui import (
    QFont, QIcon, QPixmap, QFontDatabase, QColor, QCursor
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QApplication,
    QStackedWidget, QVBoxLayout, QWidget, QProgressBar,
    QGraphicsOpacityEffect, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect, 
    QPushButton
)

from utils.settings import Settings
from cozy import AppLogger, nodal
from app_info import APP_NAME, APP_VERSION

from cozy.canvas import CozyCanvas
from cozy.node_types import WarmNode, AboutNode, ImageNode, RenderNode
from cozy.session import SessionManager, auto_backup_session
from cozy.audio import AudioFeedback
from cozy.window import ModernMainWindowMixin

class CuddlyDuddlyFuddly(QMainWindow, ModernMainWindowMixin):
    def __init__(self):
        super().__init__()
        self.logger = AppLogger.get().root_logger
        self.base_dir = Path(__file__).resolve().parent

        # 1. Identity & Gameplay State
        self.joy_buckets = 0
        self.feed_press_count = 0
        self.progress_value = 100.0
        self._scene_dirty = False
        self.hearts = []

        # 2. Styles & Geometry
        self._apply_stylesheet()
        self._restore_geometry()

        # 3. Timers & Assets
        self.breath_steps = 30
        self.breath_remaining = self.breath_steps
        self.breath_timer = QTimer(self)
        self.breath_timer.setInterval(100)
        self.breath_timer.timeout.connect(self._update_breath_display)
        self.breath_timer.start()

        # Load Icons using the base_dir to ensure they are found
        self.heart_pix = self._load_asset("Images/heart.png", 70)
        self.bullet_pix = self._load_asset("Images/bullet.png", 50)

        # 4. UI Build
        self.apply_modern_window_setup()
        self.setup_ui()

        # 5. Session Initialization
        last_session = Settings().get("last_session")
        SessionManager.refresh_session_list(self.session_combo, current_name=last_session)
        self._loading(last_session)

    def _load_asset(self, path, size):
        p = self.base_dir / path
        pix = QPixmap(str(p))
        return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation) if not pix.isNull() else QPixmap()

    def _apply_stylesheet(self):
        qss_path = self.base_dir / "styles.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
            self.logger.info("Cozy styles applied. ✨")

    def setup_ui(self) -> None:
        """Reconstructs the multi-pane layout from the 'Full Glory' version."""
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.page_canvas = QWidget()
        self.page_canvas.setObjectName("page_canvas")
        self.layout_canvas = QVBoxLayout(self.page_canvas)
        self.layout_canvas.setContentsMargins(20, 10, 20, 15)
        self.layout_canvas.setSpacing(10)

        # --- Top Bar ---
        self._setup_top_bar()

        # --- Central Content Area (Canvas + Preview) ---
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(15)

        # 1. Nodal Canvas
        canvas_panel, self.sketch_view, self.sketch_scene = CozyCanvas.create_canvas_panel(self)
        self.sketch_scene.selectionChanged.connect(self.on_node_selection_changed)
        self.sketch_scene.changed.connect(lambda: setattr(self, '_scene_dirty', True))
        self.content_layout.addWidget(canvas_panel, stretch=2) # Canvas gets more room

        # 2. Right Preview Panel
        self._setup_right_panel()
        self.layout_canvas.addLayout(self.content_layout)

        # --- Bottom Feedback & Controls ---
        self._setup_joy_meter()
        self._setup_interaction_bar()
        self._setup_action_footer()

        self.stack.addWidget(self.page_canvas)

    def _setup_top_bar(self):
        top = QHBoxLayout()
        self.session_combo = nodal.combo(items=None, fixedWidth=310, currentTextChanged=self._loading)
        top.addStretch(1)
        top.addWidget(self.session_combo)
        top.addWidget(nodal.button("Save", clicked=self._saving, fixedWidth=80))
        
        self.save_feedback = QLabel(" ✓ Saved")
        self.save_feedback.setObjectName("saveFeedbackLabel")
        self.fade_effect = QGraphicsOpacityEffect(self.save_feedback); self.fade_effect.setOpacity(0.0)
        self.save_feedback.setGraphicsEffect(self.fade_effect)
        top.addWidget(self.save_feedback)
        top.addStretch(1)
        self.layout_canvas.addLayout(top)

    def _setup_right_panel(self):
        self.right_side = QVBoxLayout()
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PreviewCard")
        self.preview_frame.setFixedWidth(400) # Match the 'Glory' width
        
        inner = QVBoxLayout(self.preview_frame)
        self.node_title_label = QLabel("Welcome 🌱")
        self.node_title_label.setObjectName("NodeTitle")
        
        self.welcome_label = QLabel("Select a node to peer inside... ✨")
        self.welcome_label.setObjectName("WelcomeLabel")
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setAlignment(Qt.AlignTop)
        
        inner.addWidget(self.node_title_label)
        inner.addWidget(nodal.scroll_area(widget=self.welcome_label))
        
        self.right_side.addWidget(self.preview_frame)
        self.right_side.addStretch(1)
        self.content_layout.addLayout(self.right_side)

    def _setup_joy_meter(self):
        joy_row = QHBoxLayout()
        joy_row.addStretch(1)
        lbl = QLabel("Buckets of Joy: "); lbl.setObjectName("joyLeftLabel")
        self.joy_label = QLabel("0"); self.joy_label.setObjectName("joyValueLabel")
        joy_row.addWidget(lbl); joy_row.addWidget(self.joy_label)
        joy_row.addStretch(1)
        self.layout_canvas.addLayout(joy_row)

    def _setup_interaction_bar(self):
        row = QHBoxLayout()
        row.addStretch(1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("mainProgressBar")
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=15, color=QColor(255,182,193,120), offset=QPoint(0,0)))

        row.addWidget(self._icon_btn(self.heart_pix, self._heart))
        row.addWidget(self._icon_btn(self.bullet_pix, self._on_feed_clicked))
        row.addWidget(self.progress_bar)
        row.addStretch(1)
        self.layout_canvas.addLayout(row)

    def _setup_action_footer(self):
        bot = QHBoxLayout()
        bot.addWidget(nodal.button("New Node", clicked=self.show_node_type_chooser))
        bot.addStretch()
        bot.addWidget(nodal.button("Settings", clicked=lambda: SettingsDialog(self).exec()))
        bot.addWidget(nodal.button("Exit", clicked=self.close))
        self.layout_canvas.addLayout(bot)

    def _icon_btn(self, pix, slot):
        btn = QPushButton()
        btn.setIcon(QIcon(pix)); btn.setIconSize(QSize(30,30))
        btn.setFixedSize(45,45); btn.setFlat(True); btn.clicked.connect(slot)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    # ── Logic Blocks ──────────────────────────────────────────────

    def on_node_selection_changed(self):
        selected = self.sketch_scene.selectedItems()
        if selected and hasattr(selected[0], 'full_text'):
            self.node_title_label.setText(selected[0].title)
            self.welcome_label.setText(selected[0].full_text)
        else:
            self.node_title_label.setText("Garden")
            self.welcome_label.setText("Select a node to peer inside... ✨")

    def _on_feed_clicked(self):
        self.breath_remaining = self.breath_steps
        self.joy_buckets += 1
        self.joy_label.setText(str(self.joy_buckets))
        try: AudioFeedback.play_joy_chime()
        except: pass

    def _update_breath_display(self):
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.breath_remaining = max(0, self.breath_remaining - 0.05)
            self.progress_bar.setValue(int((self.breath_remaining / self.breath_steps) * 100))

    def _loading(self, name):
        if not name: return
        self.logger.info(f"Loading Session: {name}")
        try:
            SessionManager.load_session(self.sketch_scene, name, view=self.sketch_view)
            self._expand_scene_to_fit_content()
        except Exception as e:
            self.logger.error(f"Session failed: {e}")

    def _saving(self):
        name = self.session_combo.currentText()
        if name:
            SessionManager.save_session(self.sketch_scene, name, view=self.sketch_view)
            anim = QPropertyAnimation(self.fade_effect, b"opacity")
            anim.setStartValue(1.0); anim.setEndValue(0.0); anim.setDuration(1500); anim.start()

    def show_node_type_chooser(self):
        # Defaulting to WarmNode for now
        node = WarmNode(node_id=random.randint(1000, 9999))
        self.sketch_scene.addItem(node)
        self._expand_scene_to_fit_content()

    def _expand_scene_to_fit_content(self, margin=250):
        items = self.sketch_scene.items()
        if not items: return
        rect = items[0].sceneBoundingRect()
        for i in items: rect = rect.united(i.sceneBoundingRect())
        self.sketch_scene.setSceneRect(self.sketch_scene.sceneRect().united(rect.adjusted(-margin,-margin,margin,margin)))

    def _save_geometry(self):
        s = Settings()
        s.set("geometry", self.saveGeometry().toHex().data().decode())
        s.set("window_state", self.saveState().toHex().data().decode())

    def _restore_geometry(self):
        s = Settings()
        geo = s.get("geometry")
        if geo: self.restoreGeometry(bytes.fromhex(geo))

    def _heart(self): self.logger.info("Heart Pulse! ❤️")
    def closeEvent(self, event): self._save_geometry(); self._saving(); event.accept()