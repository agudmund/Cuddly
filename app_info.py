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
        f"Cushions harmed: 0\n  But many were aggressively fluffed"
    )