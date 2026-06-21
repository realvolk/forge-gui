#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from .base import BaseWindow

class ResumeWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Resume Installation")
        self.add_page("Resume", self.create_resume_page())

    def create_resume_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Resume Installation</span>')
        box.append(label)

        desc = Gtk.Label()
        desc.set_text("A saved installation state was found.\n\nReview the configuration below, then click Install to continue.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_min_content_height(300)

        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.set_child(self.summary_text)
        box.append(scrolled)

        self._resume_page = box
        return box

    def run(self):
        self.update_summary()
        return super().run()

    def update_summary(self):
        """Display the saved configuration from state."""
        if not hasattr(self, 'summary_text'):
            return

        if not self.state:
            self.summary_text.get_buffer().set_text("No saved state found.")
            return

        summary = "Saved Installation Configuration:\n\n"
        key_order = [
            ("DISK", "Disk"),
            ("FS_TYPE", "Filesystem"),
            ("BOOTLOADER", "Bootloader"),
            ("INIT", "Init System"),
            ("KERNEL_CHOICE", "Kernel"),
            ("WM_DE", "Desktop"),
            ("DISPLAY_MANAGER", "Display Manager"),
            ("X_STACK", "Display Stack"),
            ("NETWORK_STACK", "Network Stack"),
            ("AUDIO_STACK", "Audio Stack"),
            ("USER_SHELL", "User Shell"),
            ("PRIV_ESCALATION", "Privilege Escalation"),
            ("USE_LUKS", "LUKS Encryption"),
            ("USE_LVM", "LVM"),
            ("GENERATE_UKI", "UKI"),
            ("HOSTNAME", "Hostname"),
            ("TIMEZONE", "Timezone"),
            ("LOCALE", "Locale"),
            ("KEYMAP", "Keyboard Layout"),
            ("USER_NAME", "Username"),
            ("EXTRAS", "Extra Packages"),
        ]

        for key, label in key_order:
            value = self.state.get(key, "Not set")
            if value:
                summary += f"  {label}: {value}\n"

        stage = self.state.get("INSTALL_STAGE", "")
        if stage:
            summary += f"\nResuming from stage: {stage}"

        self.summary_text.get_buffer().set_text(summary)

    def collect_state(self):
        self.state['MODE'] = 'resume'
        self.state['GUI_MODE'] = 'yes'

    def start_installation(self):
        self.collect_state()
        self.save_state()
        self.run_installer()