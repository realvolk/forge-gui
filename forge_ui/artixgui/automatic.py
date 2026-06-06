#!/usr/bin/env python3
import subprocess
from gi.repository import Gtk
from .base import BaseWindow, CommonPages

class AutomaticWindow(BaseWindow, CommonPages):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Automatic Installation")
        self.add_page("Welcome", self.create_welcome_page())
        self.add_page("Theme", self.create_theme_page())
        self.add_page("Disk & Partitioning", self.create_disk_page())   # full disk page
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
        # Full disk page with swap, LUKS, LVM
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label(label="Select target disk:", xalign=0)
        box.pack_start(label, False, False, 0)
        
        disk_store = Gtk.ListStore(str, str)
        result = subprocess.run(['lsblk', '-dpno', 'NAME,SIZE,MODEL', '-e', '7'], 
                               capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                name = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
                disk_store.append([name, rest])
        
        self.disk_combo = Gtk.ComboBox.new_with_model(disk_store)
        renderer_text = Gtk.CellRendererText()
        self.disk_combo.pack_start(renderer_text, True)
        self.disk_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.disk_combo, False, False, 0)
        
        self.swap_check = Gtk.CheckButton(label="Create swap partition")
        box.pack_start(self.swap_check, False, False, 5)
        
        self.luks_check = Gtk.CheckButton(label="Enable LUKS encryption")
        box.pack_start(self.luks_check, False, False, 5)
        
        self.luks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.luks_box.set_margin_start(20)
        pass_label = Gtk.Label(label="LUKS Passphrase:", xalign=0)
        self.luks_box.pack_start(pass_label, False, False, 0)
        self.luks_pass_entry = Gtk.Entry()
        self.luks_pass_entry.set_visibility(False)
        self.luks_pass_entry.set_invisible_char("*")
        self.luks_box.pack_start(self.luks_pass_entry, False, False, 0)
        confirm_label = Gtk.Label(label="Confirm Passphrase:", xalign=0)
        self.luks_box.pack_start(confirm_label, False, False, 0)
        self.luks_confirm_entry = Gtk.Entry()
        self.luks_confirm_entry.set_visibility(False)
        self.luks_confirm_entry.set_invisible_char("*")
        self.luks_box.pack_start(self.luks_confirm_entry, False, False, 0)
        box.pack_start(self.luks_box, False, False, 0)
        self.luks_box.set_visible(False)
        self.luks_check.connect("toggled", self.on_luks_toggled)
        
        self.lvm_check = Gtk.CheckButton(label="Enable LVM")
        box.pack_start(self.lvm_check, False, False, 5)
        
        return box
    
    def on_luks_toggled(self, check):
        self.luks_box.set_visible(check.get_active())

    def create_privilege_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        priv_label = Gtk.Label(label="Privilege escalation:", xalign=0)
        box.pack_start(priv_label, False, False, 0)
        
        priv_store = Gtk.ListStore(str)
        for priv in ["sudo", "doas"]:
            priv_store.append([priv])
        
        self.priv_combo = Gtk.ComboBox.new_with_model(priv_store)
        renderer_text = Gtk.CellRendererText()
        self.priv_combo.pack_start(renderer_text, True)
        self.priv_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.priv_combo, False, False, 0)
        
        self.arch_repos_check = Gtk.CheckButton(label="Enable Arch Linux repositories")
        box.pack_start(self.arch_repos_check, False, False, 5)
        
        self.offline_check = Gtk.CheckButton(label="Enable offline installation mode (cached packages)")
        box.pack_start(self.offline_check, False, False, 5)
        
        return box

    def collect_state(self):
        # First collect all common fields
        self.collect_state_common()
        self.state['MODE'] = 'auto'
        
        # Then add automatic-specific fields
        if hasattr(self, 'disk_combo'):
            iter = self.disk_combo.get_active_iter()
            if iter:
                self.state['DISK'] = self.disk_combo.get_model()[iter][0]
        
        if hasattr(self, 'swap_check'):
            self.state['SWAP_ENABLED'] = "yes" if self.swap_check.get_active() else "no"
        
        if hasattr(self, 'luks_check'):
            self.state['USE_LUKS'] = "yes" if self.luks_check.get_active() else "no"
            if hasattr(self, 'luks_pass_entry') and self.luks_check.get_active():
                self.state['LUKS_PASS'] = self.luks_pass_entry.get_text()
        
        if hasattr(self, 'lvm_check'):
            self.state['USE_LVM'] = "yes" if self.lvm_check.get_active() else "no"