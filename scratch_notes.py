
    def _toggle_breath_pulse(self, enable: bool):
        if enable and self.progress_bar.value() == 100:
            if not self.pulse_anim.state() == QPropertyAnimation.Running:
                self.progress_bar.setGraphicsEffect(self.breath_glow)
                self.pulse_anim.start()
                # Optional: very gentle scale pulse
                rect = self.progress_bar.geometry()
                self.pulse_scale.setStartValue(rect)
                self.pulse_scale.setEndValue(rect.adjusted(2, 2, -2, -2))  # tiny breathe in/out
                self.pulse_scale.start()
        else:
            self.pulse_anim.stop()
            self.pulse_scale.stop()
            self.progress_bar.setGraphicsEffect(None)

    def _drain_breath(self):
        if self.breath_remaining == 0:
            if self.progress_bar.value() > 0:
                new_value = max(0, self.progress_bar.value() - 1)  # gentle drain
                self.progress_anim.setStartValue(self.progress_bar.value())
                if new_value < 100:
                    self._toggle_breath_pulse(False)
                self.progress_anim.setEndValue(new_value)
                self.progress_anim.start()
                self.progress_value = new_value  # keep in sync

    def _check_full_breath_time(self):
        if self.progress_bar.value() == 100:
            self.time_at_full += 1
            if self.time_at_full >= 30:  # 30 seconds at full
                self.add_joy_bucket(1)
                self._toggle_breath_pulse(True)
                self.time_at_full = 0  # reset counter after reward
                # Optional: visual/audio reward
                from cozy.audio import AudioFeedback
                AudioFeedback.play_new_node_chime()
                # self._apply_progress_glow() if you have the glow effect
        else:
            self.time_at_full = 0  # reset if breath drops

    def _apply_progress_glow(self):
        self.progress_bar.setGraphicsEffect(self.progress_glow)
        QTimer.singleShot(2000, lambda: self.progress_bar.setGraphicsEffect(None))  # glow for 2s

    def add_joy_bucket(self, amount=1):
        self.joy_buckets += amount
        # Cap at 10 buckets for a full bar cycle
        # target_progress = (self.joy_buckets % 10) * 10
        # self.progress_anim.setStartValue(self.progress_bar.value())
        # self.progress_anim.setEndValue(target_progress)
        # self.progress_anim.start()  # ← animate the change
        # if target_progress == 100:
        #     from cozy.audio import AudioFeedback
        #     AudioFeedback.play_new_node_chime()
        #     self._apply_progress_glow()
        #     self._joy_burst()
        #     QMessageBox.information(self, "Joy Overflow! ✨", "You've filled a bucket of joy — keep creating!")

    def _update_joy_display(self):
        if hasattr(self, 'joy_label'):
            self.joy_label.setText(f"Buckets of joy: {self.joy_buckets}")      

    def _feed_essence(self):
        # print("feed press count:",self.feed_press_count)
        
        if self.feed_press_count >= 3:
            return

        self.feed_press_count += 1

        if self.progress_value < 100:
            target_value = min(100.0, self.progress_bar.value() + 10.0)
            self.progress_anim.setStartValue(self.progress_bar.value())
            self.progress_anim.setEndValue(int(target_value))
            self.progress_anim.start()  # ← animate the fill
            self.progress_value = target_value

        # Gentle feedback
        self.welcome_label.setText("A little spark added — some joy restored! ✨")
        QTimer.singleShot(2000, lambda: self.welcome_label.setText(""))

        # Start or extend cooldown if needed
        if self.feed_press_count == 3:
            # First press → start 10-second window
            self.feed_cooldown_timer.start(3000)
            self.feed_press_count = 0

        # Optional chime or pulse here later

    def _check_joy_accumulation(self):
        """Every second: if bar is full, count up; after 30s → +1 bucket of joy."""
        self._update_breath_display()
        if self.progress_value >= 100.0:
            self.full_duration_counter += 1
            if self.full_duration_counter >= 30:
                self.joy_buckets += 1
                self.full_duration_counter = 0  # reset counter for next bucket
                self._update_joy_display()

                # Costumary tiny celebration
                self.welcome_label.setText(f"+1 bucket of joy! ✨ ({self.joy_buckets})")
                QTimer.singleShot(3000, lambda: self.welcome_label.setText(""))
        else:
            self.full_duration_counter = 0  # reset if not full