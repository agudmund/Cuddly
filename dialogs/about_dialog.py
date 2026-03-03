#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Jacket - dialogs/about_dialog.py
  A warm little about dialog for enjoying. 
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve

from cozy import nodal
from utils.settings import Settings
from app_info import APP_NAME, get_full_version, get_about_text


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Geometry memory (just like Settings now) ─────────────────────
        geometry = Settings.get("about_dialog/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(460, 380)                    # cozy starting size

        self.setWindowTitle(f"About {APP_NAME} ✨")
        self.setMinimumSize(420, 340)
        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Title
        title = QLabel(APP_NAME)
        title.setFont(QFont("Lato", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Version
        version = QLabel(get_full_version())
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #8a7a67; font-size: 14px;")
        layout.addWidget(version)

        layout.addSpacing(12)

        # Braincell line
        braincell = QLabel("Built using a single shared braincell")
        braincell.setAlignment(Qt.AlignCenter)
        braincell.setStyleSheet("font-size: 15px; font-weight: bold; color: #fff;")
        layout.addWidget(braincell)

        # About text
        about_label = QLabel(get_about_text())
        about_label.setAlignment(Qt.AlignCenter)
        about_label.setWordWrap(True)
        about_label.setStyleSheet("color: #d0d0d0; font-size: 13px; line-height: 1.4;")
        layout.addWidget(about_label)

        layout.addStretch()

        # ── Cozy button area ────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        close_btn = nodal.button("Close", clicked=self.close)
        close_btn.setFixedWidth(120)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        nodal.gentle_fade_in(self, 420)

    def closeEvent(self, event):
        """Remember position so it feels like home next time"""
        Settings.set("about_dialog/geometry", self.saveGeometry())
        Settings.sync()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """Escape = gentle close"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)