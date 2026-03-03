#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  The Jacket - utils/helpers.py
  Shared gentle helper functions used across the app 🌱
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

from pathlib import Path
import hashlib


class Helpers:
    @staticmethod
    def get_content_hash(text: str) -> str:
        """Generates a unique, stable ID based on content — perfect for tracking nodes and layout positions 🌱"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    @staticmethod
    def get_project_root() -> Path:
        """Returns the root folder of the project — our cozy central hearth 🏡"""
        return Path(__file__).parent.parent.resolve()