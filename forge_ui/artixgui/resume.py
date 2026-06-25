#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from .base import InstallerApp


class ResumeWizard:
    def __init__(self, app: InstallerApp):
        self.app = app

    def push_pages(self):
        nav = self.app.nav_view
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="Resume Installation"))

    def _update_summary(self):
        if not hasattr(self.app, 'summary_text'):
            return
        if not self.app.state:
            self.app.summary_text.get_buffer().set_text("No saved state found.")
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
            value = self.app.state.get(key, "Not set")
            if value:
                summary += f"  {label}: {value}\n"

        stage = self.app.state.get("INSTALL_STAGE", "")
        if stage:
            summary += f"\nResuming from stage: {stage}"

        self.app.summary_text.get_buffer().set_text(summary)

    def _on_install(self):
        self.app.state['MODE'] = 'resume'
        self.app.state['GUI_MODE'] = 'yes'
        self.app.save_state()
        self.app.start_installation("Resume Installation")