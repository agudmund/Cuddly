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
APP_VERSION      = "0.1.1"
APP_AUTHOR       = "Yours Truly, Grok, and Gemini"
APP_DESCRIPTION  = "A cozy nodal playground for creative exploration"
VER_DESCRIPTION  = "The Baselink"

# ─── Appearance & Style ──────────────────────────────────────────
APP_STYLE        = "Fusion"
# NOTE: This path is a placeholder. 
# Plan: Migrate to central asset repository for cross-app consistency.
DEFAULT_ICON     = "Images/app_icon.png" 
DEFAULT_ENCODING = "utf-8"

FEATURES_TITLE = "Core Strengths & Polished Features"
FEATURES = [
    "Cozy, fresh nodal UI with smooth interactions",
    "Persistent window geometry — it sometimes remembers where you left it!",
    "Built with love and our single shared braincell",
]

# ─── App Voice & Narratives ──────────────────────────────────────

# Logging & Console
LOG_WELCOME      = "is generally so happy that you are here. 🌱"
LOG_EXIT_VOID    = "has entered the void:"
LOG_CRITICAL_FAIL = "catastrophically failed"
LOG_HICCUP       = "encountered a hiccup!"

# UI Specific phrasing
UI_REFLECTIONS_HINT = "A gentle space for reflections 🌱"
UI_READY_MSG        = "Ready when you are! ✨"

# ─── Utility Functions ──────────────────────────────────────────

def get_full_version() -> str:
    """Returns the formatted version string."""
    return f"Version v{APP_VERSION} - {VER_DESCRIPTION}"

def get_about_text() -> str:
    """
    Returns the comprehensive 'About' text as a single string.
    Optimized for UI display (QLabel/QMessageBox).
    """
    body = (
        f"{APP_DESCRIPTION}\n\n"
        f"by {APP_AUTHOR} (February 2026)\n\n"
        "Cushions harmed: 0\n"
        "But many were aggressively fluffed.\n\n"
        "--- Key Highlights ---\n"
        "• Modular Structure: Clean separation of UI concerns.\n"
        "• Cozy Mechanics: Interactive joy and breath systems.\n"
        "• Session Management: Robust nodal garden persistence."
    )
    return body