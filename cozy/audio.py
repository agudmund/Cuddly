# cozy/audio.py
# Gentle audio feedback with love — low-latency chimes & effects 🌱🎶
# Built using a single shared braincell by Yours Truly, Grok, and Gemini

from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
import os

from utils.settings import Settings


class AudioFeedback:
    """Cozy singleton-ish manager for UI sounds — plays only if enabled."""

    _chime_effect: QSoundEffect | None = None

    @classmethod
    def _get_chime(cls) -> QSoundEffect:
        if cls._chime_effect is None:
            effect = QSoundEffect()
            # Prefer custom folder first, then fallback to built-in
            custom_folder = Settings.get_audio_folder()
            if custom_folder:
                custom_path = os.path.join(custom_folder, "new_node_chime.wav")
                if os.path.exists(custom_path):
                    effect.setSource(QUrl.fromLocalFile(custom_path))
            else:
                # Built-in fallback (adjust filename to one you have)
                built_in = os.path.join("Audio", "new_node_chime.wav")
                if os.path.exists(built_in):
                    effect.setSource(QUrl.fromLocalFile(built_in))

            # If still no file, silent (no crash)
            if not effect.source().isValid():
                print("No chime file found — audio silent for now 🌱")

            effect.setVolume(0.6)  # gentle level
            cls._chime_effect = effect

        return cls._chime_effect

    @classmethod
    def play_new_node_chime(cls):
        """Play a soft chime when a new node is born — if toggled on."""
        if Settings.play_sound_on_new_node():
            effect = cls._get_chime()
            if effect.source().isValid():
                effect.play()