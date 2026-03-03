#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Participants are the best Pants - Cozy Times cozy/nodal.py
  Cozy node helpers & UI bits for enjoying — simple creations with love 🌱
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

from PySide6.QtWidgets import QPushButton, QWidget, QComboBox, QScrollArea, QProgressBar
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class CozyButton(QPushButton):
    """Warm little button with cozy defaults 🌿"""
    def __init__(self, text="Click me 🌱", parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(100)
        self.setMinimumHeight(36)

        # Gentle cozy styling — matched to your app's dark theme
        self.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #6b5a47;
                border-radius: 6px;
                color: #e0f0e0;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #555555;
                border: 2px solid #8a7a67;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
            }
        """)

        # Friendly font tweak
        font = self.font()
        font.setPointSize(13)
        self.setFont(font)

class CozyComboBox(QComboBox):
    """
    Warm combo box that looks and feels exactly like CozyButton 🌿
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(36)
        self.setFont(QFont("Lato", 13))  # matches the rest of the app

        # Same cozy palette, bevel, and hover magic as your buttons
        self.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #6b5a47;
                border-radius: 6px;
                color: #e0f0e0;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                background-color: #444444;
            }
            QComboBox:pressed, QComboBox:on {
                background-color: #555555;
                border: 2px solid #8a7a67;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
                background: transparent;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                image: none;  /* clean look — you can add a tiny ↓ later if you want */
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a3a;
                border: 1px solid #6b5a47;
                border-radius: 6px;
                color: #e0f0e0;
                selection-background-color: #444455;
                selection-color: #ffffff;
                padding: 4px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3a3a3a;
            }
        """)


def combo(
    items: list[str] = None,
    current_text: str = None,
    parent=None,
    **kwargs
) -> QComboBox:
    """
    Creates a fresh cozy combo box ready for layouts — exactly like nodal.button().
    Special support for 'currentTextChanged=slot' and 'currentIndexChanged=slot'.
    """
    cbox = CozyComboBox(parent)

    if items:
        cbox.addItems(items)

    if current_text:
        cbox.setCurrentText(current_text)

    # Connect signals if passed
    for signal_name, slot in kwargs.items():
        if signal_name in ("currentTextChanged", "currentIndexChanged"):
            signal = getattr(cbox, signal_name)
            signal.connect(slot)

    # Any other kwargs (fixedWidth, etc.)
    for key, value in kwargs.items():
        if key not in ("currentTextChanged", "currentIndexChanged"):
            setter_name = f"set{key[0].upper() + key[1:]}"
            setter = getattr(cbox, setter_name, None)
            if setter and callable(setter):
                setter(value)

    return cbox

def button(
    text: str = "Click me 🌿",
    parent=None,
    **kwargs
) -> QPushButton:
    """
    Creates a fresh cozy button ready for layouts.
    Special support for 'clicked=slot' (connects the clicked signal).
    Other kwargs are passed to setters (e.g. fixedWidth=120, icon=..., etc.)
    """
    btn = CozyButton(text, parent)

    # Handle signal connections first
    if "clicked" in kwargs:
        slot = kwargs.pop("clicked")
        if slot is not None:
            btn.clicked.connect(slot)

    # Then apply remaining kwargs as setters
    for key, value in kwargs.items():
        setter_name = f"set{key[0].upper() + key[1:]}"
        setter = getattr(btn, setter_name, None)
        if setter and callable(setter):
            setter(value)

    return btn

class SmoothScrollArea(QScrollArea):
    """A QScrollArea that animates scrolling for a buttery-smooth feel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.butterscroll_effect = 250
        self._scroll_anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self._scroll_anim.setDuration(self.butterscroll_effect)
        self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        current_val = self.verticalScrollBar().value()
        target_val = current_val - delta
        target_val = max(0, min(target_val, self.verticalScrollBar().maximum()))
        
        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(current_val)
        self._scroll_anim.setEndValue(target_val)
        self._scroll_anim.start()

def scroll_area(widget: QWidget = None, parent=None, **kwargs) -> SmoothScrollArea:
    sa = SmoothScrollArea(parent)
    sa.setWidgetResizable(kwargs.pop("widgetResizable", True)) 

    if widget:
        sa.setWidget(widget)
    
    # Apply standard setters (fixedWidth, etc.)
    for key, value in kwargs.items():
        setter_name = f"set{key[0].upper() + key[1:]}"
        setter = getattr(sa, setter_name, None)
        if setter and callable(setter):
            setter(value)
    return sa

def gentle_fade_in(widget, duration_ms: int = 420) -> None:
    """
    Plays a gentle window fade-in. Safe to call multiple times
    Never restarts mid-fade.
    """
    if hasattr(widget, "_fade_anim") and widget._fade_anim.state() == QPropertyAnimation.State.Running:
        return

    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    anim.start()

    # Keep reference so we don't accidentally start another one
    widget._fade_anim = anim

def cozy_dialog(cls, parent=None, **kwargs):
    attr_name = f'_{cls.__name__.lower()}_dialog'
    
    dialog = None
    if hasattr(parent, attr_name):
        candidate = getattr(parent, attr_name)
        # Check if object is still alive (not deleted)
        if hasattr(candidate, 'isVisible') or hasattr(candidate, 'show'):
            dialog = candidate
        else:
            # Clean up dead reference
            delattr(parent, attr_name)
    
    if dialog is None or dialog.isHidden():
        dialog = cls(parent, **kwargs)
        dialog.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        # Optional: keep WA_DeleteOnClose if you want, but then never reuse dead ones
        # dialog.setAttribute(Qt.WA_DeleteOnClose)
        gentle_fade_in(dialog)
        dialog.show()
        dialog.raise_()
        if parent is not None:
            setattr(parent, attr_name, dialog)
    else:
        dialog.raise_()
        dialog.activateWindow()

class CozyProgressBar(QProgressBar):
    """Warm progress bar with cozy defaults, animations, and glow effects 🌿"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(False)  # clean look — add if you want percentages
        self.setFixedHeight(12)     # slim and cozy
        self.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: 1px solid #6b5a47;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background-color: #ff69b4;  /* hot pink for joy! */
                border-radius: 5px;
            }
        """)

        # Fill animation
        self.progress_anim = QPropertyAnimation(self, b"value")
        self.progress_anim.setDuration(1200)
        self.progress_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # Pulse/glow when full
        self.breath_glow = QGraphicsDropShadowEffect()
        self.breath_glow.setBlurRadius(15)
        self.breath_glow.setColor(QColor(255, 182, 193, 180))  # soft pink
        self.breath_glow.setOffset(0, 0)

        self.pulse_anim = QPropertyAnimation(self, b"graphicsEffect")
        self.pulse_anim.setDuration(2000)
        self.pulse_anim.setStartValue(None)
        self.pulse_anim.setEndValue(self.breath_glow)
        self.pulse_anim.setLoopCount(-1)  # gentle pulsing forever until stopped

        # Optional scale pulse (subtle size breathe)
        self.pulse_scale = QPropertyAnimation(self, b"geometry")
        self.pulse_scale.setDuration(2000)
        self.pulse_scale.setLoopCount(-1)

def progress_bar(
    parent=None,
    minimum=0,
    maximum=100,
    value=0,
    **kwargs
) -> CozyProgressBar:
    """
    Creates a fresh cozy progress bar ready for layouts 🌿
    Just like button() or combo() — with support for setters like fixedWidth=300.
    """
    pbar = CozyProgressBar(parent)
    pbar.setMinimum(minimum)
    pbar.setMaximum(maximum)
    pbar.setValue(value)

    # Apply any extra kwargs (e.g., fixedWidth=300)
    for key, val in kwargs.items():
        setter_name = f"set{key[0].upper() + key[1:]}"
        setter = getattr(pbar, setter_name, None)
        if setter and callable(setter):
            setter(val)

    return pbar