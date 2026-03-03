#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  The Jacket - dialogs/settings_dialog.py
  The cozy beautiful settings home
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QStyle,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLayout,
    QFrame, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QIcon

from utils.settings import Settings
from utils.helpers import Helpers

from dialogs.about_dialog import AboutDialog

from cozy import nodal

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        geometry = Settings.get("settings_dialog/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(520, 520)

        self.setWindowTitle("The Glorious Settings!")
        self.setMinimumSize(480, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setStyleSheet("background-color: #1e1e1e; color: #e0e0e0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(22)

        self.project_root = Helpers.get_project_root()

        qpush = """
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #6b5a47;
                border-radius: 6px;
                color: #e0f0e0;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #444444; }
            QPushButton:disabled { background-color: #2a2a2a; color: #666666; }
        """
        qpushinactive = """
                    QPushButton {
                        background-color: #2a2a2a;
                        border: 1px solid #4a3a2f;
                        border-radius: 6px;
                        color: #a08a7a;
                        padding: 4px 8px;
                        font-size: 13px;
                    }
                    QPushButton:hover { background-color: #333333; color: #e0e0e0; }
                """

        # ── App Icon Section ──────────────────────────────────────────
        app_row = QHBoxLayout()
        app_row.setSpacing(12)

        app_title = QLabel("App Window Icon")
        app_title.setFont(QFont("Lato", 14, QFont.Bold))
        app_row.addWidget(app_title)

        app_row.addStretch()

        self.app_status = QLabel("No custom icon set")
        self.app_status.setStyleSheet("color: #8a7a67; font-size: 13px;")
        app_row.addWidget(self.app_status)

        app_row.addSpacing(16)

        app_cluster = QHBoxLayout()
        app_cluster.setSpacing(8)

        self.app_preview = QLabel()
        self.app_preview.setFixedSize(32, 32)
        self.app_preview.setAlignment(Qt.AlignCenter)
        app_cluster.addWidget(self.app_preview)

        choose_app = nodal.button("Choose", clicked=self.choose_app_icon)
        choose_app.setFixedHeight(28)
        choose_app.setFixedWidth(70)

        reset_app = nodal.button("Reset", clicked=lambda: self.reset_icon("icon_path", self.app_status, self.app_preview))
        reset_app.setFixedHeight(28)
        reset_app.setFixedWidth(70)

        for btn in (choose_app, reset_app):
            btn.setStyleSheet( qpush)
            if btn.text() == "Reset":
                btn.setStyleSheet( qpushinactive)

        app_cluster.addWidget(choose_app)
        app_cluster.addWidget(reset_app)

        app_row.addLayout(app_cluster)
        layout.addLayout(app_row)

        # ── Bullet Icon Section ───────────────────────────────────────
        bullet_row = QHBoxLayout()
        bullet_row.setSpacing(12)

        bullet_title = QLabel("Feature List Bullet Icon")
        bullet_title.setFont(QFont("Lato", 14, QFont.Bold))
        bullet_row.addWidget(bullet_title)

        bullet_row.addStretch()

        self.bullet_status = QLabel("Using default")
        self.bullet_status.setStyleSheet("color: #8a7a67; font-size: 13px;")
        bullet_row.addWidget(self.bullet_status)

        bullet_row.addSpacing(16)

        bullet_cluster = QHBoxLayout()
        bullet_cluster.setSpacing(8)

        self.bullet_preview = QLabel()
        self.bullet_preview.setFixedSize(32, 32)
        self.bullet_preview.setAlignment(Qt.AlignCenter)
        bullet_cluster.addWidget(self.bullet_preview)

        choose_bullet = nodal.button("Choose", clicked=self.choose_bullet_icon)
        choose_bullet.setFixedHeight(28)
        choose_bullet.setFixedWidth(70)
        bullet_cluster.addWidget(choose_bullet)

        reset_bullet = nodal.button("Reset", clicked=lambda: self.reset_icon("bullet_icon_path", self.bullet_status, self.bullet_preview))
        reset_bullet.setFixedHeight(28)
        reset_bullet.setFixedWidth(70)
        reset_bullet.setStyleSheet(qpushinactive)

        # bullet_cluster.addWidget(choose_bullet)
        bullet_cluster.addWidget(reset_bullet)

        bullet_row.addLayout(bullet_cluster)
        layout.addLayout(bullet_row)

        # ── Audio section ──────────────────────────────────────────────────────
        audio_header = QLabel("Audio Vibes 🌸")
        audio_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #d0a080;")
        layout.addWidget(audio_header)

        self.cb_new_node_sound = QCheckBox("Play sound when creating new node")
        self.cb_new_node_sound.setChecked(Settings.play_sound_on_new_node())
        self.cb_new_node_sound.toggled.connect(
            lambda checked: Settings.set_play_sound_on_new_node(checked)
        )
        layout.addWidget(self.cb_new_node_sound)

        # Optional gentle note
        note = QLabel("A soft chime will play when you add a new thought bubble.")
        note.setStyleSheet("color: #8a7a67; font-size: 12px; font-style: italic;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addSpacing(16)

        # ── About Section (bottom cozy footer) ────────────────────────────────
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(nodal.button("About ✨", clicked=self.show_about))
        bottom_layout.addWidget(nodal.button("Close", clicked=self.close))
        layout.addLayout(bottom_layout)

        # layout.addStretch()
        self._refresh_statuses()
        nodal.gentle_fade_in(self)

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(line)

    def _get_absolute_path(self, rel_or_abs_path: str | None) -> Path:
        if not rel_or_abs_path:
            return Path()
        p = Path(rel_or_abs_path)
        if p.is_absolute():
            return p.resolve()
        return (self.project_root / p).resolve()

    def _update_icon_status(self, key: str, status_label: QLabel, preview: QLabel, default_name: str, default_filename: str):
        stored_path = Settings.get(key)
        if stored_path:
            abs_path = self._get_absolute_path(stored_path)
            if abs_path.exists():
                status_label.setText(abs_path.name)
                pix = QPixmap(str(abs_path)).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview.setPixmap(pix)
                return
        # Default fallback
        status_label.setText(default_name)
        default_path = self.project_root / default_filename
        if default_path.exists():
            pix = QPixmap(str(default_path)).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            preview.setPixmap(pix)
        else:
            preview.setText("🖼️")  # tiny cozy placeholder

    def _refresh_statuses(self):
        # App icon now uses the same key + path as the rest of the app
        self._update_icon_status("ui/icon_path", self.app_status, self.app_preview,
                                 "Using default (app_icon.png)", "Images/app_icon.png")
        
        # Bullet stays exactly as before (no change needed)
        self._update_icon_status("bullet_icon_path", self.bullet_status, self.bullet_preview,
                                 "Using default (bullet.png)", "Images/bullet.png")

    def choose_app_icon(self):
        start_dir = Settings.get_directory("last_dir_icon") or str(self.project_root)
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Select App Icon", start_dir, "Icons (*.ico *.png *.jpg *.jpeg)"
        )
        if not path_str:
            return
        chosen = Path(path_str)
        if not chosen.exists():
            return
        try:
            rel = chosen.relative_to(self.project_root).as_posix()
            Settings.set("ui/icon_path", rel)
            Settings.set_directory("last_dir_icon", str(chosen.parent))
            self._refresh_statuses()
        except ValueError:
            abs_str = str(chosen.resolve())
            Settings.set("ui/icon_path", abs_str)
            Settings.set_directory("last_dir_icon", str(chosen.parent))
            self._refresh_statuses()

        if self.parent() and hasattr(self.parent(), 'refresh_window_icon'):
            self.parent().refresh_window_icon()

    def choose_bullet_icon(self):
        start_dir = (
            Settings.get_directory("last_dir_bullet")
            or Settings.get_directory("last_dir_icon")
            or str(self.project_root)
        )
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Bullet Icon", start_dir, "Images (*.png *.ico *.jpg *.jpeg)"
        )
        if not path_str:
            return
        chosen = Path(path_str)
        if not chosen.exists():
            return
        try:
            rel = chosen.relative_to(self.project_root).as_posix()
            Settings.set("bullet_icon_path", rel)
            Settings.set_directory("last_dir_bullet", str(chosen.parent))
            self._refresh_statuses()
        except ValueError:
            abs_str = str(chosen.resolve())
            Settings.set("bullet_icon_path", abs_str)
            Settings.set_directory("last_dir_bullet", str(chosen.parent))
            self._refresh_statuses()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not set bullet icon:\n{str(e)}")

    def reset_icon(self, key: str, status_label: QLabel, preview: QLabel):
        """Reset icon and immediately refresh the live window icon."""
        if key in ("icon_path", "ui/icon_path"):
            Settings.set("ui/icon_path", None)
            if self.parent() and hasattr(self.parent(), 'refresh_window_icon'):
                self.parent().refresh_window_icon()
        self._refresh_statuses()

    def closeEvent(self, event):
        Settings.set("settings_dialog/geometry", self.saveGeometry())
        Settings.sync()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def show_about(self):
        """Open About using the cozy centralized helper"""
        nodal.cozy_dialog(AboutDialog, self)