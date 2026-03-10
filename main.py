#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Cuddly, Duddly, and Fuddy, the Wuddlies - main.py
  A warm gentle UI for enjoying.
  Built using a single shared braincell by Yours Truly, Grok, and Gemini
"""
import os
import sys
import argparse
import traceback

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from main_window import CuddlyDuddlyFuddly
from cozy import setup_logging

# Importing our Identity and our Voice constants
from app_info import (
    APP_NAME, 
    APP_VERSION, 
    APP_STYLE, 
    ORG_NAME,
    LOG_WELCOME,
    LOG_EXIT_VOID,
    LOG_CRITICAL_FAIL,
    LOG_HICCUP
)

def exception_hook(exctype, value, tb):
    """Custom hook to log and print unhandled exceptions using the app's voice."""
    print(f"{APP_NAME} {LOG_HICCUP}", file=sys.stderr)
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

sys.excepthook = exception_hook

def setup_parser():
    """Handles command line arguments for debugging."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main() -> None:
    args = setup_parser()
    debug_mode = args.debug or (os.getenv("COZY_DEBUG") == "1")
    logger = setup_logging(debug=debug_mode)

    # 1. High-DPI Setup (Required before QApplication creation)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 2. Initialization Phase
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle(APP_STYLE)
    
    logger.debug(f"Debug mode active: {debug_mode}")
    logger.info(f"{APP_NAME} {LOG_WELCOME}")

    # Initialize the UI
    window = CuddlyDuddlyFuddly()
    window.show()

    # 3. Execution Phase
    try:
        # Launch the main event loop
        sys.exit(app.exec())
    except Exception as e:
        # If the loop breaks unexpectedly, log it with our centralized phrasing
        logger.critical(f"{LOG_CRITICAL_FAIL} in {APP_NAME}", exc_info=True)
        print(f"{APP_NAME} {LOG_EXIT_VOID} {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()