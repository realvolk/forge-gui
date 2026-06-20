#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import subprocess
from gi.repository import Gtk
from .base import BaseWindow, CommonPages

class AutomaticWindow(BaseWindow, CommonPages):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Automatic Installation")
        self._init_common_pages()
        self.add_page("Welcome", self.create_welcome_page())
        self.add_page("Theme", self.create_theme_page())
        self.add_page("Disk & Partitioning", self.create_disk_page())
        self.add_page("Filesystem", self.create_filesystem_page())
        self.add_page("Bootloader", self.create_bootloader_page())
        self.add_page("Kernel", self.create_kernel_page())
        self.add_page("Init System", self.create_init_page())
        self.add_page("Desktop", self.create_desktop_page())
        self.add_page("Network & Audio", self.create_network_audio_page())
        self.add_page("Shell & Extras", self.create_extras_page())
        self.add_page("Users", self.create_users_page())
        self.add_page("Privilege & Power", self.create_privilege_page())
        self.add_page("Summary", self.create_summary_page())

    def create_disk_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label(label="Select target disk:", xalign=0)
        box.append(label)

        disk_list = Gtk.StringList.new([])
        result = subprocess.run(['lsblk', '-dpno', 'NAME,SIZE,MODEL', '-e', '7'],
                               capture_output=True, text=True)
        disk_names = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                disk_names.append(parts[0])
        if disk_names:
            disk_list = Gtk.StringList.new(disk_names)
        self.disk_combo = Gtk.DropDown.new(disk_list)
        box.append(self.disk_combo)

        self.swap_check = Gtk.CheckButton(label="Create swap partition")
        box.append(self.swap_check)

        self.luks_check = Gtk.CheckButton(label="Enable LUKS encryption")
        box.append(self.luks_check)

        self.luks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.luks_box.set_margin_start(20)
        pass_label = Gtk.Label(label="LUKS Passphrase:", xalign=0)
        self.luks_box.append(pass_label)
        self.luks_pass_entry = Gtk.PasswordEntry()
        self.luks_pass_entry.set_show_peek_icon(False)
        self.luks_box.append(self.luks_pass_entry)
        confirm_label = Gtk.Label(label="Confirm Passphrase:", xalign=0)
        self.luks_box.append(confirm_label)
        self.luks_confirm_entry = Gtk.PasswordEntry()
        self.luks_confirm_entry.set_show_peek_icon(False)
        self.luks_box.append(self.luks_confirm_entry)
        box.append(self.luks_box)
        self.luks_box.set_visible(False)
        self.luks_check.connect("toggled", self.on_luks_toggled)

        self.lvm_check = Gtk.CheckButton(label="Enable LVM")
        box.append(self.lvm_check)

        return box

    def on_luks_toggled(self, check):
        self.luks_box.set_visible(check.get_active())

    def create_privilege_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        priv_label = Gtk.Label(label="Privilege escalation:", xalign=0)
        box.append(priv_label)
        priv_list = Gtk.StringList.new(["sudo", "doas"])
        self.priv_combo = Gtk.DropDown.new(priv_list)
        box.append(self.priv_combo)

        self.arch_repos_check = Gtk.CheckButton(label="Enable Arch Linux repositories")
        box.append(self.arch_repos_check)
        self.offline_check = Gtk.CheckButton(label="Enable offline installation mode (cached packages)")
        box.append(self.offline_check)

        return box

    def collect_state(self):
        if not self.collect_state_common():
            return
        self.state['MODE'] = 'auto'

        if hasattr(self, 'disk_combo'):
            idx = self.disk_combo.get_selected()
            model = self.disk_combo.get_model()
            if 0 <= idx < model.get_n_items():
                self.state['DISK'] = model.get_string(idx)

        if hasattr(self, 'swap_check'):
            self.state['SWAP_ENABLED'] = "yes" if self.swap_check.get_active() else "no"

        if hasattr(self, 'luks_check'):
            self.state['USE_LUKS'] = "yes" if self.luks_check.get_active() else "no"
            if hasattr(self, 'luks_pass_entry') and self.luks_check.get_active():
                self.state['LUKS_PASS'] = self.luks_pass_entry.get_text()

        if hasattr(self, 'lvm_check'):
            self.state['USE_LVM'] = "yes" if self.lvm_check.get_active() else "no"