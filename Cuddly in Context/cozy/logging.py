#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Discworld - utils/logging.py
# Cozy centralized logging for enjoying.
# Handles console output + daily file logs with all the warmth
# 
# Built using a single shared braincell by Yours Truly and Grok

import os
import logging
import functools
import time
import sys

from typing import Optional
from datetime import datetime

from app_info import APP_NAME, DEFAULT_ICON

class AppLogger:
    _instance: Optional['AppLogger'] = None
    root_logger: logging.Logger

    @classmethod
    def get(cls, debug: Optional[bool] = None) -> 'AppLogger':
        if cls._instance is None:
            cls._instance = cls(debug=debug)
        else:
            # Already exists → update level if a new debug value is provided
            if debug is not None:
                cls._instance.update_debug_mode(debug)
        return cls._instance

    def update_debug_mode(self, debug: bool):
        self.debug_mode = debug
        level = logging.DEBUG if debug else logging.INFO
        self.root_logger.setLevel(level)
        
        # Also update console handler level (find it among handlers)
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
                handler.setLevel(level)
                break

    def __init__(self, debug: Optional[bool] = None):
        if hasattr(self, 'root_logger') and self.root_logger.handlers:
            return 

        self.debug_mode = debug if debug is not None else os.getenv("COZY_DEBUG", "0") == "1"

        self.root_logger = logging.getLogger(APP_NAME.lower().replace(" ", "-"))
        level = logging.DEBUG if self.debug_mode else logging.INFO
        self.root_logger.setLevel(level)

        # Clear any existing handlers to prevent duplicates on re-config
        self.root_logger.handlers.clear()

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler — match root logger level
        console_level = logging.DEBUG if self.debug_mode else logging.INFO
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(console_level)
        console.setFormatter(formatter)
        self.root_logger.addHandler(console)

        # File handler — always full DEBUG for complete records
        log_dir = self._get_log_dir()
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = os.path.join(log_dir, f"nodal-tester_{today}.log")
        file_handler = logging.FileHandler(filepath, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.root_logger.addHandler(file_handler)

    def _get_log_dir(self) -> str:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    def get_today_log_path(self) -> str:
        log_dir = self._get_log_dir()
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(log_dir, f"nodal-tester_{today}.log")

    # ── Convenience methods ────────────────────────────────────────
    def debug(self, msg: str, *args, **kwargs) -> None:
        self.root_logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.root_logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.root_logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.root_logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.root_logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log current exception with traceback."""
        self.root_logger.exception(msg, *args, **kwargs)


# Improved smarter & lighter log_call decorator
def log_call(func):
    """Gentle decorator that logs function entry/exit + duration.
    Only logs when debug mode is active, with smart truncation for readability."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = AppLogger.get()

        # Only do debug logging if enabled
        if logger.root_logger.isEnabledFor(logging.DEBUG):
            func_name = func.__name__
            # Short arg summary: type for positional, name=… for kwargs
            arg_parts = [type(a).__name__ for a in args[1:]]  # skip self for methods
            for k, v in kwargs.items():
                val_repr = "…" if isinstance(v, (str, list, dict, tuple)) and len(str(v)) > 40 else repr(v)
                arg_parts.append(f"{k}={val_repr}")
            arg_str = ", ".join(arg_parts) if arg_parts else ""

            logger.debug(f" └─ args: {args!r} | kwargs: {kwargs!r}")

        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start

            if logger.root_logger.isEnabledFor(logging.DEBUG):
                res_repr = "…" if isinstance(result, (list, dict)) and len(str(result)) > 60 else repr(result)
                logger.debug(f"← {func_name} → {res_repr} ({duration:.3f}s)")

            return result
        except Exception as e:
            duration = time.perf_counter() - start
            logger.error(f"{func_name} raised {type(e).__name__} after {duration:.3f}s", exc_info=True)
            raise
    return wrapper

# One-time setup helper (used in main.py)
def setup_logging(debug: bool = False) -> logging.Logger:
    AppLogger.get(debug=debug)
    return logging.getLogger(APP_NAME.lower().replace(" ", "-"))