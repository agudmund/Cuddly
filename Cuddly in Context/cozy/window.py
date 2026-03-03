#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cozy/window.py
Cozy modern window mixin for enjoying — reusable warmth for any QMainWindow 🌱
Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

import os
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFontDatabase
from PySide6.QtWidgets import QMainWindow

from utils.settings import Settings
from app_info import DEFAULT_ICON
from cozy import nodal, AppLogger

class ModernMainWindowMixin:
    """Gentle mixin for modern QMainWindow setup — fonts, styles, icon, geometry, fade-in ✨"""
    fade_duration_ms = 500
    default_width = 1200
    default_height = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = AppLogger.get()

    def _load_fonts(self) -> None:
        """Loads our cozy custom fonts from the fonts/ folder."""
        font_dir = os.path.join(os.path.dirname(__file__), "../fonts")
        if os.path.exists(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.lower().endswith(('.ttf', '.otf')):
                    QFontDatabase.addApplicationFont(os.path.join(font_dir, font_file))
                    self.logger.debug(f"Font loaded: {font_file}")

    def _apply_styles(self) -> None:
        """Applies our warm global stylesheet."""
        style_path = os.path.join(os.path.dirname(__file__), "../styles/styles.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
                self.logger.debug("Global stylesheet applied ✨")

    def refresh_window_icon(self) -> None:
        """Centralized: resolves and applies the current icon (custom or default)."""
        path = Settings.get_current_icon_path()
        if path and os.path.exists(path):
            icon = QIcon(path)
            self.logger.debug(f"Window icon applied: {path}")
        else:
            self.logger.debug("No custom/default icon found — using system fallback")
            icon = QIcon.fromTheme("application-x-executable")
        self.setWindowIcon(icon)

    def _restore_geometry(self) -> None:
        """Restores last window position/size or uses cozy defaults."""
        geometry = Settings.get("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(self.default_width, self.default_height)

    def apply_modern_window_setup(self) -> None:
        self._load_fonts()
        self._apply_styles()
        self.refresh_window_icon()
        self._restore_geometry()
        nodal.gentle_fade_in(self, self.fade_duration_ms)