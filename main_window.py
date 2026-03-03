#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Cuddly, Duddly, and Fuddy, the Wuddlies - main_window.py
  A warm gentle UI for enjoying.
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

import os
import random
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from PySide6.QtGui import QFont, QIcon, QPixmap, QFontDatabase, QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QApplication, QMessageBox,
    QStackedWidget, QVBoxLayout, QWidget, QProgressBar,
    QGraphicsOpacityEffect, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)

from utils.settings import Settings
from cozy import AppLogger, nodal
from app_info import APP_NAME, APP_VERSION

from cozy.canvas import CozyCanvas
from cozy.warm import WarmNode
from cozy.about import AboutNode
from cozy.session import SessionManager
from cozy.audio import AudioFeedback
from cozy.window import ModernMainWindowMixin
# from cozy.session_helpers import (
#     prompt_save_current_session,
#     save_session,
#     load_session,
#     auto_backup_session,
#     add_to_recent_sessions,
#     quick_load_most_recent,
#     get_session_filename
# )

from dialogs.settings_dialog import SettingsDialog

from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QCursor, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect

class CuddlyDuddlyFuddly(QMainWindow, ModernMainWindowMixin):
    def __init__(self):
        super().__init__()
        self.logger = AppLogger.get().root_logger
        self._restore_geometry()
        self.current_session_path = None
        self._last_known_session_name = None  # if used
        self.progress_value = 100.0
        self.progress_bar = None

        self.joy_buckets = 0
        self.full_duration_counter = 0  # seconds at 100%
        self.joy_timer = QTimer(self)
        self.joy_timer.setInterval(100)  # check every second
        # self.joy_timer.timeout.connect(self._check_joy_accumulation)

        # Feed cooldown
        self.feed_press_count = 0
        self.feed_cooldown_timer = QTimer(self)
        self.feed_cooldown_timer.setSingleShot(True)
        # self.feed_cooldown_timer.timeout.connect(self._reset_feed_cooldown)

        # Breath timer
        self.breath_steps = 30
        self.breath_remaining = self.breath_steps
        self.breath_timer = QTimer(self)
        self.breath_timer.setInterval(100)
        self.breath_timer.timeout.connect(self._update_breath_display)
        self.breath_timer.start()
        # self.joy_timer.start()

        self.progress_glow = QGraphicsDropShadowEffect()
        self.progress_glow.setBlurRadius(12)
        self.progress_glow.setColor(QColor(255, 180, 193, 160))  # soft pink glow
        self.progress_glow.setOffset(0, 0)

        # Breath drain timer (slowly depletes energy)
        self.breath_drain_timer = QTimer(self)
        # self.breath_drain_timer.timeout.connect(self._drain_breath)
        self.breath_drain_timer.start(1000)  # drain every nth seconds — adjust to taste

        # Track cumulative time spent at full breath
        self.time_at_full = 0
        self.full_breath_timer = QTimer(self)
        # self.full_breath_timer.timeout.connect(self._check_full_breath_time)
        self.full_breath_timer.start(1000)  # check every second

        self.heart_pixmap = QPixmap("Images/heart.png")
        self.heart_pix_scaled = QPixmap("Images/heart.png").scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.bullet_pix_scaled = QPixmap("Images/bullet.png").scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.hearts = []

        self.apply_modern_window_setup()
        self.setup_ui()
        self.on_load()

    # ── UI setup ────────────────────────────────────────────────────────
    def setup_ui(self) -> None:
        # 1. CORE: Setup the data containers first
        self._setup_canvas()
        self._setup_nodal_canvas() 
        
        # 2. VITALS: Setup the progress bar and animations 
        # (on_load needs self.progress_anim!)
        self._setup_main_buttons() 
        
        # 3. INTERFACE: Setup the side panels
        self._setup_right_panel()
        
        # 4. TRIGGER: Finally, setup the top bar. 
        # This will trigger the first _handle_session_switch.
        self._setup_top_bar()

        self.stack.addWidget(self.page_canvas)
        self.stack.setCurrentWidget(self.page_canvas)

        self._restore_last_session()

    def _restore_last_session(self):
        last_session = Settings().get("last_session")
        self.logger.debug(f'Restoring session {last_session}')
        
        if last_session:
            # Find the index of the last session in the combo box
            index = self.session_combo.findText(last_session)
            if index >= 0:
                # Setting this will automatically trigger the 'on_load' 
                # signal if you have it connected to currentIndexChanged
                self.session_combo.setCurrentIndex(index)
            else:
                # Fallback if the file was deleted or renamed
                self.on_load() 
        else:
            # No history? Just load whatever is first
            self.on_load()

    def _setup_canvas(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.setWindowTitle(APP_NAME)

        self.page_canvas = QWidget()
        self.page_canvas.setObjectName("page_canvas")

        self.layout_canvas = QVBoxLayout(self.page_canvas)
        self.layout_canvas.setContentsMargins(20, 20, 20, 20)
        self.layout_canvas.setSpacing(15)

    def _setup_top_bar(self):
        # Guard: If the combo already exists, we've already run this.
        if hasattr(self, 'session_combo') and self.session_combo is not None:
            return

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 12)
        top_bar.setSpacing(10)
        top_bar.addStretch(1)

        # 1. The Session Combo
        sessions = SessionManager.get_available_sessions()
        self.session_combo = nodal.combo(
            items=None,
            fixedWidth=310,
            currentTextChanged=self._handle_session_switch
        )
        self.session_combo.blockSignals(True)
        self.session_combo.addItems(sessions)
        self.session_combo.blockSignals(False)
        self.current_session_name = self.session_combo.currentText()
        top_bar.addWidget(self.session_combo)

        # 2. The Manual Save Button (using your nodal.button)
        self.save_btn = nodal.button(
            "Save", 
            clicked=lambda: self.on_save(), # Manual click saves current combo selection
            fixedWidth=80
        )
        top_bar.addWidget(self.save_btn)

        # 3. The "Saved!" Label
        self.save_feedback = QLabel(" ✓ Saved")
        self.save_feedback.setStyleSheet("color: #a3be8c; font-weight: bold; margin-left: 5px;")
        
        # Create the effect
        self.fade_effect = QGraphicsOpacityEffect(self.save_feedback)
        
        # FIX: Apply to the effect directly, not via .graphicsEffect()
        self.fade_effect.setOpacity(0.0) 
        
        # Attach it
        self.save_feedback.setGraphicsEffect(self.fade_effect)
        
        # 4. THE INSERTION: Only happens if the guard above was passed
        if hasattr(self, 'layout_canvas') and self.layout_canvas is not None:
            top_bar.addWidget(self.save_feedback)
            top_bar.addStretch(1)
            self.layout_canvas.insertLayout(0, top_bar)

    def _trigger_save_visual(self):
        # 1. Reset Opacity
        self.fade_effect.setOpacity(1.0)
        
        # 2. Setup the Fade Animation
        self.save_fade = QPropertyAnimation(self.fade_effect, b"opacity")
        self.save_fade.setDuration(1500)
        self.save_fade.setStartValue(1.0)
        self.save_fade.setEndValue(0.0)
        self.save_fade.setEasingCurve(QEasingCurve.InQuint)

        # 3. Setup the Float Animation (Moving the label up)
        # Note: We animate the 'pos' property of the widget
        self.save_move = QPropertyAnimation(self.save_feedback, b"pos")
        self.save_move.setDuration(1500)
        current_pos = self.save_feedback.pos()
        self.save_move.setStartValue(current_pos)
        self.save_move.setEndValue(QPoint(current_pos.x(), current_pos.y() - 20))
        self.save_move.setEasingCurve(QEasingCurve.OutCubic)

        # 4. Group them so they play together
        self.save_group = QParallelAnimationGroup()
        self.save_group.addAnimation(self.save_fade)
        self.save_group.addAnimation(self.save_move)
        
        # Optional: Reset position after finished so it doesn't stay 'up'
        self.save_group.finished.connect(lambda: self.save_feedback.move(current_pos))
        
        self.save_group.start()

    def _handle_session_switch(self, new_session_name):
        # Guard 1: Ensure we aren't switching to the same thing
        # if not new_session_name or new_session_name == self.current_session_name:
        #     return

        # # Guard 2: Ensure the scene is actually ready before we try to save/load
        # if not hasattr(self, 'sketch_scene') or self.sketch_scene is None:
        #     return

        self.logger.info(f"Switching from {self.current_session_name} to {new_session_name}")

        # 1. Save the OLD session
        # self.on_save(self.current_session_name)

        # 2. Update tracking and Load NEW
        # self.current_session_name = new_session_name
        self.on_load()

    def _setup_nodal_canvas(self):
        canvas_panel, self.sketch_view, self.sketch_scene = CozyCanvas.create_canvas_panel(self)
        self.sketch_scene.selectionChanged.connect(self.on_node_selection_changed)
        
        self._scene_dirty = False
        self.sketch_scene.changed.connect(lambda: setattr(self, '_scene_dirty', True))

        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(20)
        self.content_layout.addWidget(canvas_panel, stretch=1)
        self.layout_canvas.addLayout(self.content_layout)

        # Joy counter above progress bar
        joy_layout = QHBoxLayout()
        joy_layout.setContentsMargins(20, 0, 20, 4)
        joy_layout.setSpacing(12)

        joy_left = QLabel("Buckets of joy")
        joy_left.setStyleSheet("color: #ffd1dc; font-size: 14px; font-weight: bold;")
        joy_layout.addStretch(1)
        joy_layout.addWidget(joy_left)

        self.joy_label = QLabel(f"{self.joy_buckets}")
        self.joy_label.setStyleSheet("color: #ffb6c1; font-size: 14px;")
        joy_layout.addWidget(self.joy_label)

        self.layout_canvas.addLayout(joy_layout)

    def _setup_right_panel(self):
        """Sets up the preview panel using the new nodal helper."""
        self.right_side = QVBoxLayout()
        self.right_side.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.preview_frame = QFrame()
        self.preview_frame.setFixedWidth(420)
        self.preview_frame.setFixedHeight(260)
        self.preview_frame.setObjectName("PreviewCard")

        inner_layout = QVBoxLayout(self.preview_frame)
        inner_layout.setContentsMargins(16, 12, 16, 12)
        inner_layout.setSpacing(8)

        self.node_title_label = QLabel("")
        self.node_title_label.setObjectName("NodeTitle") # Style this in QSS
        self.node_title_label.setFixedHeight(24)
        self.node_title_label.setFont(QFont("Chandler42"))
        inner_layout.addWidget(self.node_title_label)

        self.welcome_label = QLabel(
            "The Cozy and Beautiful Area\n"
            "Stuff and stuff will appear here soon\n\n"
            "Ready when you are! ✨"
        )
        self.welcome_label.setObjectName("WelcomeLabel")
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.welcome_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Use the new nodal helper!
        self.scroll_area = nodal.scroll_area(
            widget=self.welcome_label,
            frameShape=QFrame.Shape.NoFrame,
            horizontalScrollBarPolicy=Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        inner_layout.addWidget(self.scroll_area)

        self.right_side.addWidget(self.preview_frame)
        self.right_side.addStretch(1)
        self.content_layout.addLayout(self.right_side)

    def _setup_main_buttons(self):
        # ── Progress bar above bottom buttons ────────────────────────────────
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(20, 8, 20, 4)
        progress_layout.addStretch(1)

        self.progress_bar = self._create_progress_bar()
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_anim.setDuration(1200)  # cozy 1.2s fill-up
        self.progress_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # Pulse/glow effect for full breath
        self.breath_glow = QGraphicsDropShadowEffect()
        self.breath_glow.setBlurRadius(15)
        self.breath_glow.setColor(QColor(255, 182, 193, 180))  # soft pink
        self.breath_glow.setOffset(0, 0)

        # 1. Attach the effect to the bar
        self.progress_bar.setGraphicsEffect(self.breath_glow)

        # 2. Animate the blurRadius property of the effect object
        self.pulse_anim = QPropertyAnimation(self.breath_glow, b"blurRadius")
        self.pulse_anim.setDuration(2000)
        self.pulse_anim.setStartValue(0) # No glow
        self.pulse_anim.setEndValue(15)  # Soft glow
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.pulse_anim.setLoopCount(-1) 
        self.pulse_anim.start()

        self.pulse_scale = QPropertyAnimation(self.progress_bar, b"geometry")
        self.pulse_scale.setDuration(2000)
        self.pulse_scale.setLoopCount(-1)

        progress_layout.addStretch(1)

        # Heart pixmap to the left of the progress bar
        self.progress_btn = self._heartbeat()
        progress_layout.addWidget(self.progress_btn)
        self.feed_btn = self._create_feed_pixmap()
        progress_layout.addWidget(self.feed_btn)        
        progress_layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        self.layout_canvas.addLayout(progress_layout)

        bottom_layout = QHBoxLayout()
        # bottom_layout.addWidget(nodal.button("New Canvas", clicked=self.new_canvas))
        bottom_layout.addWidget(nodal.button("New Node", clicked=self.show_node_type_chooser))
        bottom_layout.addWidget(nodal.button("Heart", clicked=self._heart))
        bottom_layout.addStretch()
        bottom_layout.addWidget(nodal.button("Settings", clicked=self.on_click_settings))
        bottom_layout.addWidget(nodal.button("Exid", clicked=self.close))
        self.layout_canvas.addLayout(bottom_layout)

    def _create_progress_bar(self):
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        bar.setFixedHeight(20)
        bar.setFixedWidth(300)
        bar.setStyleSheet("""
            QProgressBar { background-color: #2a2a2a; border: 1px solid #4a3a3f; border-radius: 8px; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #1e1e1e, stop:0.4 #5c3e4f,
                                            stop:0.7 #a56a85, stop:1 #d87a9e);
                border-radius: 7px;
            }
        """)
        return bar

    def show_node_type_chooser(self):
        """Tiny custom popup for choosing node type — both create WarmNode for now"""
        chooser = QWidget(self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        chooser.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        chooser.setFixedSize(500, 180)

        # Soft rounded background with drop shadow
        chooser.setStyleSheet("""
            QWidget {
                background: #2a1f24;
                border: 2px solid #5c3e4f;
                border-radius: 16px;
            }
            QLabel {
                color: #ffd1dc;
                font-family: 'Chandler42';
                font-size: 18px;
            }
            QPushButton {
                background: #4a3a3f;
                color: #ffb6c1;
                border: none;
                border-radius: 12px;
                padding: 12px;
                font-family: 'Chandler42';
                font-size: 16px;
            }
            QPushButton:hover {
                background: #6a4a5f;
            }
        """)

        # Glow effect for extra coziness
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(255, 182, 193, 140))  # soft pink
        glow.setOffset(0, 0)
        chooser.setGraphicsEffect(glow)

        layout = QVBoxLayout(chooser)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("What kind of node feels right today? ✨")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        def create_node_and_close(is_about: bool):
            center = self.sketch_view.mapToScene(self.sketch_view.viewport().rect().center())
            if is_about:
                node = AboutNode(
                    node_id=len([i for i in self.sketch_scene.items() if isinstance(i, WarmNode)]) + 1,
                    pos=center
                )
            else:
                node = WarmNode(
                    node_id=len([i for i in self.sketch_scene.items() if isinstance(i, WarmNode)]) + 1,
                    pos=center
                )
            # Future: if is_about: node.make_it_about() or AboutNode(...)
            self.sketch_scene.addItem(node)
            self.logger.info(f"New {'about' if is_about else 'normal'} node added ✨")
            if Settings.play_sound_on_new_node():
                AudioFeedback.play_new_node_chime()
            chooser.close()

        normal_btn = QPushButton("Normal 🌱")
        normal_btn.clicked.connect(lambda: create_node_and_close(False))
        btn_layout.addWidget(normal_btn)

        about_btn = QPushButton("About ❤️")
        about_btn.clicked.connect(lambda: create_node_and_close(True))
        btn_layout.addWidget(about_btn)

        layout.addLayout(btn_layout)

        global_pos = self.sketch_view.mapToGlobal(self.sketch_view.viewport().rect().center())
        chooser.move(global_pos - QPoint(chooser.width() // 2, chooser.height() // 2))

        chooser.show()
        chooser.raise_()

    def _create_feed_pixmap(self):
        """Clickable ❤️ that smoothly fades from bright to dark as the timer counts down."""
        heart_label = QLabel()
        heart_label.setFixedSize(44, 44)
        heart_label.setAlignment(Qt.AlignCenter)
        heart_label.setStyleSheet("background: transparent;")

        # Load your heart image (change path if needed)
        heart_pix = QPixmap("Images/heart.png")          # ← your actual heart file
        if heart_pix.isNull():
            # Fallback red circle if image missing
            heart_pix = QPixmap(44, 44)
            heart_pix.fill(Qt.transparent)
            painter = QPainter(heart_pix)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#ff4d94"))
            painter.drawEllipse(6, 6, 32, 32)
            painter.end()

        self.feed_pixmap = heart_pix.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        heart_label.setPixmap(self.feed_pixmap)

        # Click resets timer (same as uff button)
        heart_label.setCursor(Qt.PointingHandCursor)
        heart_label.mousePressEvent = lambda e: self._joy_burst()

        # Create opacity effect for smooth fading
        self.feed_opacity_effect = QGraphicsOpacityEffect()
        heart_label.setGraphicsEffect(self.feed_opacity_effect)
        self.feed_label = heart_label

        return heart_label

    def _joy_burst(self):
        """Lovely burst of floating hearts that explode outward from the feed button you just clicked ✨"""
        # Best parent for full-window floating magic
        parent = self.stack

        # ←←← THIS IS THE KEY CHANGE: start from the feed heart you actually pressed
        button_center = self.feed_btn.rect().center()
        start_pos = self.feed_btn.mapTo(parent, button_center)

        for _ in range(8):
            heart = QLabel(parent)
            heart.setPixmap(self.heart_pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            heart.setAttribute(Qt.WA_TransparentForMouseEvents)
            heart.setStyleSheet("background: transparent;")

            # Start right at the center of the clicked feed button with a gentle spread
            heart.move(
                start_pos.x() - random.randint(-3, 3),   # tighter spread around the button
                start_pos.y() - random.randint(5,15)
            )
            heart.show()
            heart.raise_()                     # pop to the very front

            # Nice outward wobble + upward drift
            dx = random.randint(0, 280)
            dy = random.randint(-320, -110)
            duration = 1350 + random.randint(80, 750)   # super natural feel

            # Position animation
            pos_anim = QPropertyAnimation(heart, b"pos")
            pos_anim.setDuration(duration)
            pos_anim.setStartValue(heart.pos())
            pos_anim.setEndValue(heart.pos() + QPoint(dx, dy))
            pos_anim.setEasingCurve(QEasingCurve.OutQuad)

            # Opacity fade
            opacity_effect = QGraphicsOpacityEffect(heart)
            heart.setGraphicsEffect(opacity_effect)

            fade_anim = QPropertyAnimation(opacity_effect, b"opacity")
            fade_anim.setDuration(duration)
            fade_anim.setStartValue(1.0)
            fade_anim.setEndValue(0.0)

            # Keep animations alive so they don’t get garbage-collected
            heart.pos_anim = pos_anim
            heart.fade_anim = fade_anim
            heart.opacity_effect = opacity_effect

            pos_anim.start()
            fade_anim.start()

            # Delete exactly when fade finishes
            fade_anim.finished.connect(heart.deleteLater)

        # Gentle sound
        try:
            from cozy.audio import AudioFeedback
            AudioFeedback.play_new_node_chime()
        except Exception:
            pass

    def _reset_breath_timer(self):
        self.breath_remaining = self.breath_steps
        self.breath_timer.start()

        # Bring heart back to full bright
        if hasattr(self, 'heartbeat_opacity'):
            self.heartbeat_opacity.setOpacity(1.0)
    
    def _update_breath_display(self):
        # print ('tick tick tick',self.breath_remaining,self.progress_bar.value())
        self.breath_remaining -= .1  # ← 0.1 per 100 ms tick

        # Smooth fade: opacity from 1.0 → 0.25 over time
        opacity = (self.breath_remaining / self.breath_steps) ** 2
        # opacity = max(0.25, self.breath_remaining / self.breath_steps)
        self.heartbeat_opacity.setOpacity(self.breath_remaining/self.breath_steps)
        if self.breath_remaining <= 0:
            self.heartbeat_opacity.setOpacity(1)
            self.heartbeat.setPixmap(self.bullet_pix_scaled) 
            self.breath_remaining = 0
        else:
            self.heartbeat.setPixmap(self.heart_pix_scaled)

    def _heartbeat(self):
        """Clickable ❤️ that smoothly fades from bright to dark as the timer counts down."""
        self.heartbeat = QLabel()
        self.heartbeat.setFixedSize(44, 44)
        self.heartbeat.setAlignment(Qt.AlignCenter)
        self.heartbeat.setStyleSheet("background: transparent;")

        # Click resets timer
        self.heartbeat.setCursor(Qt.PointingHandCursor)
        self.heartbeat.mousePressEvent = lambda e: self._reset_breath_timer()

        # Create opacity effect for smooth fading
        self.heartbeat_opacity = QGraphicsOpacityEffect()
        self.heartbeat.setGraphicsEffect(self.heartbeat_opacity)

        return self.heartbeat

    # ── UI events ────────────────────────────────────────────────────────
    def new_node(self) -> None:
        center = self.sketch_view.mapToScene(self.sketch_view.viewport().rect().center())
        node = WarmNode(
            node_id=len([i for i in self.sketch_scene.items() if isinstance(i, WarmNode)]) + 1,
            pos=center
        )
        self.sketch_scene.addItem(node)
        self.logger.info("New warm node added ✨")
        self.welcome_label.setText("New warm node created — double-click to edit! 🌱")
        if Settings.play_sound_on_new_node():
            AudioFeedback.play_new_node_chime()
            self.logger.info("♪ gentle new-node chime would play here ♪")

    def on_node_selection_changed(self):
        try:
            selected = self.sketch_scene.selectedItems()
        except RuntimeError as e:
            selected = []

        # 1. Handle Reset / No valid node selected
        if not selected or not isinstance(selected[0], (WarmNode, AboutNode)):
            self.node_title_label.setText("")
            self.welcome_label.setText("The Cozy and Beautiful Area\nReady when you are! ✨")
            return

        # 2. Handle any supported node selection
        node = selected[0]
        title = node.title.strip() if node.title else "Untitled note"
        
        # Optional: make About nodes feel a bit more special in the label
        if isinstance(node, AboutNode):
            prefix = "📌 "   # or ❤️ or 🌿 — whatever feels right
            title = prefix + title
            # You could also add a small note if you want
            body = node.full_text.strip() or "A gentle space for reflections 🌱"
            self.node_title_label.setText(f" {title}")
        else:
            body = node.full_text.strip() or "This note is delightfully empty 🌱"
            self.node_title_label.setText(f" ❤️ {title}")
        self.welcome_label.setText(body)
        self._expand_scene_to_fit_content(margin=500)

    def on_click_settings(self):
        """Open the glorious settings window using the cozy centralized helper"""
        nodal.cozy_dialog(SettingsDialog, self)

    def _restore_geometry(self):
        """Restore last saved window position and size if available."""
        geometry_hex = Settings().get("window_geometry")
        if geometry_hex and isinstance(geometry_hex, str):
            try:
                geometry_bytes = bytes.fromhex(geometry_hex)
                if self.restoreGeometry(geometry_bytes):
                    if Settings().get("window_maximized", False):  self.showMaximized()
                    self.logger.debug("Window geometry restored successfully 🌱")
                else:
                    self.logger.debug("Stored geometry was invalid — using default")
            except Exception as e:
                self.logger.warning(f"Failed to restore geometry: {e} — using default")
        else:
            self.logger.debug("No saved geometry found — starting fresh")

        if not geometry_hex:
            self.setGeometry(300, 200, 1200, 800)  # your preferred cozy default size
            self.move(QApplication.primaryScreen().availableGeometry().center() - self.rect().center())

        Settings().sync()

    def closeEvent(self, event):
        # if self._scene_dirty:
            # reply = QMessageBox.question(self, "Unsaved changes", 
            #                              "Save current session before closing? 🌱",
            #                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            # if reply == QMessageBox.Cancel:
            #     event.ignore()
            #     return
            # if reply == QMessageBox.Yes:
            #     if self.current_session_path:
            #         save_session(self.sketch_scene, self.current_session_path, ...)
            #     else:
        self.on_save()
                        # save_session(self.sketch_scene, save_path, ...)
        Settings().set("window_geometry", self.saveGeometry().toHex().data().decode())
        super().closeEvent(event)

    # def closeEvent(self, event):
    #     # Remember the session
    #     Settings().set("last_session", self.session_combo.currentText())
        
    #     # Remember the window size/position
    #     Settings().set("window_geometry", self.saveGeometry().toHex().data().decode())
    #     Settings().set("window_maximized", self.isMaximized())
        
    #     self.logger.info(f"Exid: {self.session_combo.currentText()} ✨")
    #     super().closeEvent(event)

    def on_save(self, session_name=None):
        # If no name is passed (manual click), use the one currently in the combo box
        # name_to_save = session_name if session_name else self.session_combo.currentText()
        
        # Crucial: get_session_filename must receive the name_to_save
        path = 'sessions/'+self.session_combo.currentText()+'.json'
        
        # if path:
        # Get current view state for the camera
        view_center = self.sketch_view.mapToScene(self.sketch_view.viewport().rect().center())
        view_zoom = self.sketch_view.transform().m11()

        success = SessionManager.save_session(
            self.sketch_scene,
            path,
            view=self.sketch_view,
            progress_value=self.progress_value,
            joy_buckets=self.joy_buckets,
            camera_pos=(view_center.x(), view_center.y()),
            camera_zoom=view_zoom
        )
        # if success:
        self.logger.info(f"Saved session: {path}")
        # print("Inside foo, caller is:", self.get_caller_name_ctypes())

                # self._scene_dirty = False
                # self._trigger_save_visual() # Show the "Saved!" feedback
    # ?

    # def get_caller_name_ctypes(self):
    #     import ctypes
    #     # Get the current frame
    #     frame = ctypes.pythonapi.PyEval_GetFrame()
    #     if not frame:
    #         return "<no frame>"

    #     # Go one level up
    #     prev_frame = ctypes.cast(frame, ctypes.py_object).value.f_back
    #     if not prev_frame:
    #         return "<top-level>"

    #     code = prev_frame.f_code
    #     return code.co_name
    def on_load(self):
        # if self._scene_dirty:
            # save_path = self.current_session_path)
            # if save_path is None:
            #     self.logger.debug("Session switch cancelled to save current 🌱")
                # return  # Abort load if user cancels prompt

            # Actually save the current before clearing
            # if save_session(self.sketch_scene, save_path, self.sketch_view, 
            #                 self.progress_value, self.joy_buckets):
            #     self._scene_dirty = False  # Reset after successful save
            #     self.current_session_path = save_path  # Update path if new
            # else:
            #     self.logger.warning("Save failed during switch — aborting load")
            #     return  # Don't proceed if save fails

        # Now safe to clear and load
        current_text = self.session_combo.currentText()
        target = 'sessions/'+current_text+'.json'
        
        if not target or not os.path.exists(target):
            self.logger.warning(f"Invalid load path: {target} — skipping")
            return

        self.sketch_scene.clear()
        data = SessionManager.load_session(self.sketch_scene, filepath=target, view=self.sketch_view)
        if data:
            # Update UI as before
            self.progress_value = data.get("progress_value", 100.0)
            if self.progress_anim and self.progress_bar:
                self.progress_anim.stop()
                self.progress_anim.setStartValue(self.progress_bar.value())
                self.progress_anim.setEndValue(int(self.progress_value))
                self.progress_anim.start()
            self.joy_buckets = data.get("joy_buckets", 0)
            self.joy_label.setText(f"{self.joy_buckets}")
            Settings().set("last_session", current_text)
            self.current_session_path = Path(target)  # Track new path
            self._scene_dirty = False  # Clean after load
        else:
            self.logger.info("Load returned no data — adding gentle default node ✨")
            # If you have a add_default_node() method, call it here
            # self.add_welcome_node()

    def add_welcome_node(self):
        node = WarmNode(node_id=1, title="All Glory", full_text=" and that.", pos=QPointF(0, 0))
        self.sketch_scene.addItem(node)
        self._expand_scene_to_fit_content()    

    # def on_load(self):
    #     # if self._scene_dirty:
    #     #     if not prompt_save_current_session(self.sketch_scene):  # assuming it returns True if saved/canceled
    #     #         return  # abort load if user cancels
    #     current_text = self.session_combo.currentText()
    #     target = get_session_filename(current_text)
        
    #     if not target or not os.path.exists(target):
    #         return

    #     # Clear the scene for the new session
    #     if self.sketch_scene:
    #         self.sketch_scene.clear()

    #     # SessionManager.load_session returns the full data dict 
    #     # and handles view.centerOn internally if you pass 'view'
    #     data = SessionManager.load_session(self.sketch_scene, filepath=target, view=self.sketch_view)
    #     Settings().set("last_session", current_text)

    #     if data:
    #         # Update UI elements from the loaded data
    #         target_value = data.get("progress_value", 100.0)
    #         self.progress_value = target_value # Keep internal value in sync
            
    #         if hasattr(self, 'progress_anim') and self.progress_bar:
    #             self.progress_anim.stop()
    #             self.progress_anim.setStartValue(self.progress_bar.value())
    #             self.progress_anim.setEndValue(int(target_value))
    #             self.progress_anim.start()

    #         self.joy_buckets = data.get("joy_buckets", 0)
    #         self.joy_label.setText(f"{self.joy_buckets}")


    def _on_auto_backup(self):
        if self._scene_dirty:
            auto_backup_session(self.sketch_scene)
            self._scene_dirty = False

    # ── Heart methods ─────────────────────────────────────
    def _heart(self) -> None:
        # your existing heart dialog code
        pass

    def _expand_scene_to_fit_content(self, margin=250):
        """Grows the scene rect to include all items + margin for breathing room."""
        items = self.sketch_scene.items()
        if not items:
            return
        
        # Union all item bounding rects (in scene coordinates)
        union_rect = items[0].sceneBoundingRect()
        for item in items[1:]:
            union_rect = union_rect.united(item.sceneBoundingRect())
        
        # Add cozy margin (adjustable per call)
        expanded = union_rect.adjusted(-margin, -margin, margin, margin)
        
        # Only grow outward — never shrink the scene
        current = self.sketch_scene.sceneRect()
        new_rect = current.united(expanded)
        
        if new_rect != current:
            self.sketch_scene.setSceneRect(new_rect)
            self.logger.info(f"Expanded canvas to {new_rect.width()}x{new_rect.height()} ✨")