#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  The Jacket - utils/spellchecker.py
  Spell checking highlighter and suggestion utilities for enjoying
  Built using a single shared braincell by Yours Truly, Grok, And Gemini
"""

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import QMenu

try:
    import enchant
    ENCHANT_AVAILABLE = True
except ImportError:
    ENCHANT_AVAILABLE = False

class SpellHighlighter(QSyntaxHighlighter):
    """Highlights misspelled words with red wavy underline."""

    def __init__(self, document):
        super().__init__(document)
        self.dictionary = enchant.Dict("en_US") if ENCHANT_AVAILABLE else None

        self.misspelled_format = QTextCharFormat()
        self.misspelled_format.setUnderlineColor(QColor("#ff5555"))
        self.misspelled_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

    def highlightBlock(self, text):
        if not self.dictionary:
            return

        expression = QRegularExpression(r"\b[a-zA-Z']+\b")
        iterator = expression.globalMatch(text)

        while iterator.hasNext():
            match = iterator.next()
            word = match.captured(0)
            start = match.capturedStart()
            length = match.capturedLength()

            if not self.dictionary.check(word):
                self.setFormat(start, length, self.misspelled_format)


def show_spell_suggestions(text_edit, pos):
    """Show right-click context menu with spell suggestions."""
    if not ENCHANT_AVAILABLE:
        return

    cursor = text_edit.cursorForPosition(pos)
    cursor.select(QTextCursor.WordUnderCursor)
    word = cursor.selectedText().strip()

    if not word:
        return

    dictionary = enchant.Dict("en_US")
    if dictionary.check(word):
        return  # Correct word → no menu

    suggestions = dictionary.suggest(word)

    menu = QMenu(text_edit)
    if suggestions:
        for suggestion in suggestions[:10]:
            action = menu.addAction(suggestion)
            action.triggered.connect(lambda checked, s=suggestion, c=cursor: replace_word(c, s))
    else:
        menu.addAction("(no suggestions)").setEnabled(False)

    menu.exec(text_edit.mapToGlobal(pos))


def replace_word(cursor, suggestion):
    """Replace selected word with suggestion."""
    cursor.beginEditBlock()
    cursor.removeSelectedText()
    cursor.insertText(suggestion)
    cursor.endEditBlock()