#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  The Jacket - utils/settings.py
  Unified, cozy settings using QSettings – platform-native persistence
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

import base64
import os
from typing import Any, Optional, cast

from PySide6.QtCore import QSettings

from app_info import ORG_NAME, APP_NAME, DEFAULT_ICON, DEFAULT_ENCODING
# from cozy.logging import AppLogger
from cozy import AppLogger 

class Settings:
    """Cozy, singleton-style wrapper around QSettings with app-specific convenience methods.

    Use only via class methods: Settings.get(...), Settings.set(...), etc.
    Guarantees a single QSettings instance and thread-safe typical usage.
    """

    _settings: Optional[QSettings] = None
    _logger = None

    @classmethod
    def _get_logger(cls):
        """Lazy logger — created only when first needed."""
        if cls._logger is None:
            cls._logger = AppLogger.get().root_logger
        return cls._logger

    @classmethod
    def ensure_first_launch_defaults(cls):
        """Set sensible defaults on first launch (idempotent — safe to call anytime)."""
        if not cls.get("ui/icon_path"):
            cls.set_icon_path(DEFAULT_ICON)
            cls._get_logger().info(f"First launch defaults applied, icon path: {DEFAULT_ICON}")
        # Future defaults can be added here

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazy initialization of the real QSettings object."""
        if cls._settings is None:
            cls._settings = QSettings(ORG_NAME, APP_NAME)
            cls._get_logger().debug(f"QSettings initialized for {ORG_NAME}/{APP_NAME}")
            cls.ensure_first_launch_defaults()          # Apply defaults automatically
            cls._settings.sync()

    # ── Core access ──────────────────────────────────────────────────────────

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Retrieve a value, returning default if key is missing or value is None."""
        cls._ensure_initialized()
        assert cls._settings is not None
        value = cls._settings.value(key, default)
        cls._get_logger().debug(f"Settings.get '{key}' → {value!r}")
        return value

    @classmethod
    def set(cls, key: str, value: Any) -> bool:
        """Store a value – returns True if successful."""
        cls._ensure_initialized()
        assert cls._settings is not None
        cls._settings.setValue(key, value)
        success = cls._settings.status() == QSettings.Status.NoError
        if not success:
            cls._get_logger().warning(
                f"Failed to set '{key}' (QSettings status: {cls._settings.status()})"
            )
        else:
            cls._get_logger().debug(f"Settings.set '{key}' OK")
        return success

    @classmethod
    def remove(cls, key: str) -> None:
        """Delete a specific key."""
        cls._ensure_initialized()
        assert cls._settings is not None
        cls._settings.remove(key)
        cls._get_logger().debug(f"Settings removed key: {key}")

    @classmethod
    def clear(cls) -> None:
        """Wipe all settings (use with care!)."""
        cls._ensure_initialized()
        assert cls._settings is not None
        cls._settings.clear()
        cls._get_logger().warning("All settings cleared — destructive action completed")

    # ── Masking helpers (lightweight obfuscation) ────────────────────────────

    @classmethod
    def _mask(cls, text: str) -> str:
        if not text:
            return ""
        return base64.b64encode(text.encode(DEFAULT_ENCODING)).decode(DEFAULT_ENCODING)

    @classmethod
    def _unmask(cls, masked_text: str) -> str:
        if not masked_text:
            return ""
        try:
            return base64.b64decode(masked_text.encode(DEFAULT_ENCODING)).decode(DEFAULT_ENCODING)
        except Exception as e:
            cls._get_logger().warning(f"Failed to unmask value (returning raw): {e}")
            return masked_text

    @classmethod
    def get_masked(cls, key: str, default: str = "") -> str:
        masked = cast(str, cls.get(key, default=default))
        return cls._unmask(masked) if masked else default

    @classmethod
    def set_masked(cls, key: str, value: str) -> bool:
        masked = cls._mask(value)
        return cls.set(key, masked)

    # ── Directory helpers ────────────────────────────────────────────────────

    @classmethod
    def get_directory(cls, key: str, default: str = "") -> str:
        path = cast(str, cls.get(key, default))
        if path and isinstance(path, str) and os.path.isdir(path):
            return path
        return ""

    @classmethod
    def set_directory(cls, key: str, filepath: str) -> bool:
        if not filepath:
            return False
        dirname = os.path.dirname(filepath)
        return cls.set(key, dirname) if dirname else False

    # ── Audio helpers ────────────────────────────────────────────────────────

    @classmethod
    def get_audio_folder(cls, default: str = "") -> str:
        """Returns the custom audio folder path (or empty string if none set)."""
        return cast(str, cls.get("audio/custom_folder", default))

    @classmethod
    def set_audio_folder(cls, path: str) -> bool:
        """Sets the custom audio folder path."""
        if not path:
            return False
        success = cls.set("audio/custom_folder", path)
        if success:
            cls._get_logger().info(f"Custom audio folder set to: {path}")
        return success

    # ── Icon helpers ─────────────────────────────────────────────────────────

    @classmethod
    def get_icon_path(cls, default: str = DEFAULT_ICON) -> str:
        """Get stored icon path; falls back to default and removes bad path if missing."""
        path = cast(str, cls.get("ui/icon_path", default))

        if path != default and path and not os.path.exists(path):
            cls._get_logger().warning(
                f"Stored icon path does not exist → fallback + remove: {path}"
            )
            cls.remove("ui/icon_path")
            return default

        return path

    @classmethod
    def set_icon_path(cls, path: str) -> bool:
        """Set a custom icon path (absolute or relative)."""
        if not path:
            cls._get_logger().warning("Attempted to set empty icon path — ignored")
            return False

        if not os.path.exists(path):
            cls._get_logger().warning(f"Icon path does not exist yet, still saving: {path}")

        success = cls.set("ui/icon_path", path)
        if success:
            cls._get_logger().info(f"Icon path set to: {path}")
        return success

    # ── Audio helpers ────────────────────────────────────────────────────────

    @classmethod
    def play_sound_on_new_node(cls, default: bool = True) -> bool:
        """Should we play a pleasant chime when creating a new node?"""
        return bool(cls.get("audio/play_on_new_node", default))

    @classmethod
    def set_play_sound_on_new_node(cls, enabled: bool) -> bool:
        return cls.set("audio/play_on_new_node", enabled)

    # ── Icon helper (single source of truth) ────────────────────────────────

    @classmethod
    def get_current_icon_path(cls) -> str:
        """Returns the currently active icon path (custom > default > empty)."""
        return cls.get_icon_path()  # re-uses the existing robust logic
        
    # ── Sync / flush ─────────────────────────────────────────────────────────

    @classmethod
    def sync(cls) -> None:
        """Manually sync settings to disk."""
        if cls._settings is not None:
            cls._settings.sync()
            cls._get_logger().debug("Settings manually synced to disk")