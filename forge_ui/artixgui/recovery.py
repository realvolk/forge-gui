#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import os
import subprocess
from gi.repository import Gtk, Adw
from .base import InstallerApp


class RecoveryWizard:
    def __init__(self, app: InstallerApp):
        self.app = app

    def push_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self._create_options_page(), title="Recovery Options"))
        nav.push(Adw.NavigationPage(child=self._create_status_page(), title="System Status"))
        nav.push(Adw.NavigationPage(child=self._create_repair_page(), title="Repair Issues"))
        nav.push(Adw.NavigationPage(child=self._create_fs_repair_page(), title="Filesystem Repair"))
        nav.push(Adw.NavigationPage(child=self._create_untrusted_page(), title="Untrusted Recovery"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self.app.summary_text.get_buffer().set_text(
            "Select an action from the Recovery Options page and press Install to execute it."
        )
        nav.push(Adw.NavigationPage(child=summary_page, title="Recovery"))

    def _create_options_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Recovery Action")
        actions = [
            "View system status",
            "Repair detected issues",
            "Fix everything (kernel, initramfs, GRUB, fstab)",
            "Repair filesystem corruption",
            "Scan for rootkits",
            "Untrusted Recovery (rootkit hunt + malware scan)",
            "Full reinstall (run installer)"
        ]
        self.app.action_combo = Gtk.DropDown.new(Gtk.StringList.new(actions))
        row = Adw.ActionRow(title="Action", subtitle="What should be done?")
        row.add_suffix(self.app.action_combo)
        group.add(row)
        page.add(group)
        return page

    def _create_status_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="System Status")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(400)
        self.app.status_text = Gtk.TextView()
        self.app.status_text.set_editable(False)
        self.app.status_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.set_child(self.app.status_text)
        group.add(scrolled)

        refresh_btn = Gtk.Button(label="Refresh Status")
        refresh_btn.connect("clicked", self._on_refresh_status)
        group.add(refresh_btn)

        page.add(group)
        return page

    def _on_refresh_status(self, widget):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_dir = os.path.join(base_dir, "..", "scripts")
        cmd = ["bash", "-c", f"source {script_dir}/recovery/core.sh && recovery_get_status"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            clean = ''.join(c for c in (result.stdout or "No installation found at /mnt.") if c.isprintable() or c in '\n\r\t ')
            self.app.status_text.get_buffer().set_text(clean)
        except Exception as e:
            self.app.status_text.get_buffer().set_text(f"Error fetching status: {e}")

    def _create_repair_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Repair Detected Issues")
        desc = Gtk.Label()
        desc.set_text(
            "This will surgically fix only what's broken:\n"
            "- fstab UUIDs\n"
            "- Pacman locks and missing base\n"
            "- Missing kernel/initramfs\n"
            "- EFI boot entries\n"
            "- cryptdevice parameters\n"
            "- encrypt hooks"
        )
        desc.set_wrap(True)
        group.add(desc)
        page.add(group)
        return page

    def _create_fs_repair_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Filesystem Repair")
        self.app.fs_method_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Safe – non-destructive check",
            "Destructive – aggressive repair (may discard data)"
        ]))
        row = Adw.ActionRow(title="Repair approach")
        row.add_suffix(self.app.fs_method_combo)
        group.add(row)
        page.add(group)
        return page

    def _create_untrusted_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Untrusted Recovery")
        desc = Gtk.Label()
        desc.set_markup(
            '<span foreground="red">⚠ DANGEROUS OPERATION ⚠</span>\n\n'
            'This is intended for systems you believe may be compromised.\n\n'
            'What it will do:\n'
            '• Run a rootkit scan (rkhunter)\n'
            '• Check for common malware indicators\n'
            '• Optionally scan with ClamAV\n\n'
            'It will NOT modify your filesystem or attempt repairs.\n'
            'You run this AT YOUR OWN RISK.'
        )
        desc.set_wrap(True)
        group.add(desc)

        self.app.clamav_switch = Gtk.Switch()
        clamav_row = Adw.ActionRow(title="Run ClamAV scan", subtitle="Slow, requires ClamAV")
        clamav_row.add_suffix(self.app.clamav_switch)
        group.add(clamav_row)

        page.add(group)
        return page

    def _on_install(self):
        idx = self.app.action_combo.get_selected()
        actions = [
            "View system status", "Repair detected issues",
            "Fix everything (kernel, initramfs, GRUB, fstab)",
            "Repair filesystem corruption", "Scan for rootkits",
            "Untrusted Recovery (rootkit hunt + malware scan)",
            "Full reinstall (run installer)"
        ]
        action = actions[idx] if 0 <= idx < len(actions) else actions[0]
        self.app.state['RECOVERY_ACTION'] = action
        self.app.state['MODE'] = 'recovery'
        self.app.state['GUI_MODE'] = 'yes'
        self.app.save_state()
        self.app.start_installation("Recovery Mode")