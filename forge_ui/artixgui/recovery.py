#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import os
import subprocess
from gi.repository import Gtk
from .base import BaseWindow
from ..backends.gui import ProgressWindow

class RecoveryWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Recovery Mode")
        self.add_page("Recovery Options", self.create_options_page())
        self.add_page("System Status", self.create_status_page())
        self.add_page("Repair Issues", self.create_repair_page())
        self.add_page("Filesystem Repair", self.create_fs_repair_page())
        self.add_page("Untrusted Recovery", self.create_untrusted_page())

    def create_options_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Recovery Mode</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Select an action:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        actions = [
            "View system status",
            "Repair detected issues",
            "Fix everything (kernel, initramfs, GRUB, fstab)",
            "Repair filesystem corruption",
            "Scan for rootkits",
            "Untrusted Recovery (rootkit hunt + malware scan)",
            "Full reinstall (run installer)"
        ]
        self.action_combo = Gtk.DropDown.new(Gtk.StringList.new(actions))
        box.append(self.action_combo)
        return box

    def create_status_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">System Status</span>')
        box.append(label)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(400)
        self.status_text = Gtk.TextView()
        self.status_text.set_editable(False)
        self.status_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.set_child(self.status_text)
        box.append(scrolled)
        refresh_btn = Gtk.Button(label="Refresh Status")
        refresh_btn.connect("clicked", self.on_refresh_status)
        box.append(refresh_btn)
        return box

    def on_refresh_status(self, widget):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_dir = os.path.join(base_dir, "..", "scripts")
        cmd = ["bash", "-c", f"source {script_dir}/recovery/core.sh && recovery_get_status"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            clean = ''.join(c for c in (result.stdout or "No installation found at /mnt.") if c.isprintable() or c in '\n\r\t ')
            self.status_text.get_buffer().set_text(clean)
        except Exception as e:
            self.status_text.get_buffer().set_text(f"Error fetching status: {e}")

    def create_repair_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Repair Detected Issues</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("This will surgically fix only what's broken:\n- fstab UUIDs\n- Pacman locks and missing base\n- Missing kernel/initramfs\n- EFI boot entries\n- cryptdevice parameters\n- encrypt hooks")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        return box

    def create_fs_repair_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Filesystem Repair</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Select repair approach:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.fs_method_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Safe – non-destructive check",
            "Destructive – aggressive repair (may discard data)"
        ]))
        box.append(self.fs_method_combo)
        return box

    def create_untrusted_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Untrusted Recovery</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_markup('<span foreground="red">⚠ DANGEROUS OPERATION ⚠</span>\n\nThis is intended for systems you believe may be compromised.\n\nWhat it will do:\n• Run a rootkit scan (rkhunter)\n• Check for common malware indicators\n• Optionally scan with ClamAV\n\nIt will NOT modify your filesystem or attempt repairs.\nYou run this AT YOUR OWN RISK.')
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_wrap(True)
        box.append(desc)
        self.clamav_check = Gtk.CheckButton(label="Run ClamAV scan (slow, requires ClamAV)")
        self.clamav_check.set_active(False)
        box.append(self.clamav_check)
        return box

    def collect_state(self):
        idx = self.action_combo.get_selected()
        actions = [
            "View system status", "Repair detected issues",
            "Fix everything (kernel, initramfs, GRUB, fstab)",
            "Repair filesystem corruption", "Scan for rootkits",
            "Untrusted Recovery (rootkit hunt + malware scan)",
            "Full reinstall (run installer)"
        ]
        action = actions[idx] if 0 <= idx < len(actions) else actions[0]
        self.state['RECOVERY_ACTION'] = action
        self.state['MODE'] = 'recovery'
        self.state['GUI_MODE'] = 'yes'

    def start_installation(self):
        self.collect_state()
        self.save_state()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        install_script = os.path.join(base_dir, "..", "install")
        self.window.hide()
        progress = ProgressWindow(
            {"title": "Recovery Mode", "command": ["sudo", install_script, "--non-interactive"]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()
        if result.get("result") == "success":
            msg = "Recovery completed."
        else:
            msg = "Recovery failed. Check logs."
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
                                   message_type=Gtk.MessageType.INFO if result.get("result") == "success" else Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK, text=msg)
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())

    def on_next(self, widget):
        self.start_installation()