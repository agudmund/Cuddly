#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Cuddly, Duddly, and Fuddy, the Wuddlies - app_info.py
  A minor UI for enjoying
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

# ─── Core Identity ───────────────────────────────────────────────
APP_NAME         = "Cuddly, Duddly, and Fuddy, the Wuddlies"
ORG_NAME         = "Single Shared Braincell"
APP_VERSION      = "0.0.3"
APP_AUTHOR       = "Yours Truly, Grok, and Gemini"
APP_DESCRIPTION  = "A cozy nodal playground for creative exploration"
VER_DESCRIPTION  = "The Interlinking Era"

# ─── Appearance & Style ──────────────────────────────────────────
APP_STYLE        = "Fusion"
DEFAULT_ICON     = "Images/app_icon.png"
DEFAULT_ENCODING = "utf-8"

FEATURES_TITLE = "Core Strengths & Polished Features"
FEATURES = [
    "Cozy, fresh nodal UI with smooth interactions",
    "Persistent window geometry — it sometimes remembers where you left it!",
    "Built with love and our single shared braincell",
]

# ─── Utility Functions ──────────────────────────────────────────

def get_full_version() -> str:
    return f"Version v{APP_VERSION} - {VER_DESCRIPTION}"

def get_about_text() -> str:
    return (
        f"{APP_DESCRIPTION}\n\n"
        f"by {APP_AUTHOR} (February 2026)\n\n"
        f"Cushions harmed: 0\n  But many were aggressively fluffed",
        "Modular Structure: The separation into methods like _setup_canvas(), _setup_nodal_canvas(), _setup_right_panel(), and _setup_top_bar() makes it easy to follow and extend. Grouping 'CORE', 'VITALS', 'INTERFACE', and 'TRIGGER' in setup_ui() is a smart way to build progressively — it ensures dependencies (like progress_anim) are ready before they're needed.",
        "Cozy Mechanics: The breath/joy/full_breath timers, progress glow with QGraphicsDropShadowEffect, and heart animations create a truly immersive, positive vibe. Things like _expand_scene_to_fit_content() with its outward-only growth and margin for 'breathing room' are thoughtful touches that align perfectly with the project's spirit.",
        "Session Management: Integrating SessionManager for save/load/auto-backup is robust. Passing view/zoom/camera_pos in saves ensures a seamless reload — users will feel right at home returning to their nodal garden. The dirty flag (_scene_dirty) prevents unnecessary saves, which is efficient.",
        "UI Polish: Using QGraphicsOpacityEffect, QEasingCurve for animations, and drop shadows adds that soft, modern feel. The breath drain and full_breath accumulation encourage gentle engagement without pressure. Loading fonts (Chandler42.otf) and styles (styles.qss) via helpers keeps the window looking inviting.",
        "Error Handling & Logging: The logger is woven in nicely (e.g., info on expansions/saves), and closeEvent saves geometry/session — a great tie-in to the warm node about persistence.",
        "Optimistic Touches: Messages like 'A gentle space for reflections 🌱' and the joy/heart systems radiate positivity. The audio feedback (chimes on nodes) and visual cues (hearts scaling) make interactions feel rewarding and fun."
    )