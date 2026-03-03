#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Cushions - cozy/worker.py
# Pure minimal generic background worker template
# Built using a single shared braincell by Yours Truly and Grok

from PySide6.QtCore import QObject, Signal, Slot


class UploadWorker(QObject):
    """Ultra-minimal worker — only threads the task. Zero hard-coded logic inside run() 🌱"""
    progress_updated = Signal(int)
    total_updated = Signal(int)
    status_updated = Signal(str)
    finished = Signal(int, str)
    error_occurred = Signal(str)

    def __init__(self, task_func):
        super().__init__()
        self.task_func = task_func   # task_func will receive the worker itself and do everything

    @Slot()
    def run(self):
        """Only processes the task into the thread — exactly as you wanted ❤️"""
        try:
            self.task_func(self)   # task gets full worker to emit any signal it needs
        except Exception as e:
            self.error_occurred.emit(str(e))