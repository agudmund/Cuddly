#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# The Jacket - main.py
# A warm gentle UI for enjoying.
# Built using a single shared braincell by Yours Truly, Grok, and Gemini

import os
import sys
import argparse

from main_window import TheJacket
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from cozy import setup_logging

from app_info import APP_NAME, APP_VERSION, APP_STYLE, ORG_NAME
import sys
import traceback

def exception_hook(exctype, value, tb):
    print('Exception occurred!', file=sys.stderr)
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

sys.excepthook = exception_hook
def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    return args

def main() -> None:
    args = setup_parser()
    debug_mode = args.debug or (os.getenv("COZY_DEBUG") == "1")
    logger = setup_logging(debug=debug_mode)

    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORG_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setStyle(APP_STYLE)

        if debug_mode:
            logger.info(f"debug mode: {debug_mode}")
        logger.info(f"{APP_NAME} is generally so happy that you are here. 🌱")

        window = TheJacket()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Starting {APP_NAME} catastrophically failed", exc_info=True)
        print(f"{APP_NAME} has entered the void: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()