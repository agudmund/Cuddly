#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cozy/session_helpers.py
Reusable session utilities — prompt, load, save, recent tracking, auto-backup 🌱
Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from cozy.session import SessionManager
from utils.settings import Settings
from app_info import APP_NAME
from cozy import AppLogger

logger = AppLogger.get()


def get_session_filename(session_name: str) -> str:
    """Returns the standard filename for a session (e.g., 'Cozy Times.json')."""
    return f"sessions/{session_name}.json"

def prompt_save_current_session(current_path: Optional[Path] = None) -> Optional[Path]:
    """
    Prompts user for save location if no path is known yet.
    Returns the chosen Path or None if cancelled.
    """
    if current_path and current_path.exists():
        return current_path

    suggested = Path(f"{APP_NAME} - Untitled.json")
    path_str, _ = QFileDialog.getSaveFileName(
        None,
        "Save cozy session ✨",
        str(suggested),
        "JSON Files (*.json)"
    )

    if path_str:
        path = Path(path_str)
        logger.debug(f"User chose save path: {path}")
        return path

    logger.debug("Save cancelled by user")
    return None


def prompt_load_session() -> Optional[Path]:
    """
    Prompts user to select a session file to load.
    Returns the chosen Path or None if cancelled.
    """
    path_str, _ = QFileDialog.getOpenFileName(
        None,
        "Load cozy session ✨",
        "",
        "JSON Files (*.json)"
    )

    if path_str:
        path = Path(path_str)
        if path.exists():
            logger.debug(f"User selected load path: {path}")
            return path
        else:
            logger.warning(f"Selected file does not exist: {path}")
            QMessageBox.warning(None, "Not found", f"File not found:\n{path}")
            return None

    logger.debug("Load cancelled by user")
    return None


def quick_load_most_recent() -> Optional[Path]:
    """
    Attempts to load the most recently used session from settings.
    Returns the path if found and valid, otherwise None.
    """
    recent = Settings.get("session/recent", [])
    if not recent:
        logger.debug("No recent sessions found")
        return None

    last_path = Path(recent[0])
    if last_path.exists():
        logger.debug(f"Quick-loading most recent: {last_path}")
        return last_path
    else:
        logger.debug(f"Most recent session no longer exists: {last_path}")
        return None


def add_to_recent_sessions(filepath: Path) -> None:
    """Adds a filepath to the recent sessions list (keeps top 5)."""
    recent: List[str] = Settings.get("session/recent", [])
    str_path = str(filepath.resolve())

    if str_path in recent:
        recent.remove(str_path)

    recent.insert(0, str_path)
    Settings.set("session/recent", recent[:5])
    Settings.sync()
    logger.debug(f"Added to recent sessions (top 5): {str_path}")


def save_session(
    scene,
    path: Path,
    view=None,
    progress_value: float = 100.0,
    joy_buckets: int = 0
) -> bool:
    """
    Saves the current scene + metadata to disk.
    Updates recent list on success.
    Returns True if saved successfully.
    """
    try:
        SessionManager.save_session(
            scene,
            str(path),
            view=view,
            progress_value=progress_value,
            joy_buckets=joy_buckets
        )
        add_to_recent_sessions(path)
        logger.info(f"Session saved successfully: {path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to save session {path}: {e}", exc_info=True)
        QMessageBox.warning(None, "Save failed", f"Could not save session:\n{str(e)}")
        return False


def load_session(
    scene,
    view=None,
    path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Loads a session from disk into the given scene and view.
    Returns a dict with loaded metadata (progress_value, joy_buckets, etc.).
    Returns empty dict on failure.
    """
    if not path:
        path = quick_load_most_recent()
        if not path:
            path = prompt_load_session()
            if not path:
                logger.debug("No session selected for loading")
                return {}

    try:
        path = Path(path)
        data = SessionManager.load_session( scene, path, view)
        add_to_recent_sessions(path)
        logger.info(f"Session loaded successfully: {path}")
        return data
    except Exception as e:
        logger.warning(f"Failed to load session {path}: {e}", exc_info=True)
        QMessageBox.warning(None, "Load failed", f"Could not load session:\n{str(e)}")
        return {}


def auto_backup_session(
    scene,
    backup_dir: str = "backups",
    prefix: str = "auto",
    max_backups: int = 5
) -> Optional[Path]:
    """
    Creates a timestamped auto-backup.
    Keeps only the last max_backups files.
    Returns the backup path on success, None on failure.
    """
    try:
        backup_dir_path = Path(backup_dir)
        backup_dir_path.mkdir(parents=True, exist_ok=True)

        timestamp = AppLogger.get_timestamp("%Y%m%d_%H%M%S")
        backup_name = f"{prefix}_{APP_NAME}_{timestamp}.json"
        backup_path = backup_dir_path / backup_name

        SessionManager.save_session(scene, str(backup_path))
        logger.debug(f"Auto-backup created: {backup_path}")

        # Clean up old backups
        backups = sorted(backup_dir_path.glob(f"{prefix}_*.json"), key=os.path.getmtime)
        for old in backups[:-max_backups]:
            old.unlink()
            logger.debug(f"Removed old backup: {old}")

        return backup_path
    except Exception as e:
        logger.warning(f"Auto-backup failed: {e}", exc_info=True)
        return None