#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
import subprocess
from gi.repository import Gtk
from .automatic import AutomaticWindow

class ManualWindow(AutomaticWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state)
        self.window.set_title("Manual Installation")
        # Replace the disk page (page index 2) with manual version
        self.stack.remove(self.pages[2])
        self.pages[2] = self.create_manual_disk_page()
        self.stack.add_titled(self.pages[2], "Manual Disk", "Manual Disk")
        self.stack.set_visible_child(self.pages[0])
    
    def create_manual_disk_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Manual Partitioning</span>')
        box.pack_start(label, False, False, 0)
        
        desc = Gtk.Label()
        desc.set_text(
            "You will partition the disk yourself using tools like cfdisk or fdisk.\n\n"
            "After partitioning, the installer will continue automatically.\n\n"
            "Select the disk you want to partition:"
        )
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        
        disk_store = Gtk.ListStore(str, str)
        result = subprocess.run(
            ['lsblk', '-dpno', 'NAME,SIZE,MODEL', '-e', '7'],
            capture_output=True, text=True
        )
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
        
        reminder = Gtk.Label()
        reminder.set_text(
            "\nReminder: If you want swap, LUKS encryption, or LVM,\n"
            "you must set them up manually before continuing."
        )
        reminder.set_justify(Gtk.Justification.CENTER)
        box.pack_start(reminder, False, False, 10)
        
        return box
    
    def collect_state(self):
        # Collect all common fields from AutomaticWindow (which calls collect_state_common)
        if not self.collect_state_common():
            return
        self.state['MODE'] = 'manual'
        
        # Disk selection
        if hasattr(self, 'disk_combo'):
            it = self.disk_combo.get_active_iter()
            if it:
                self.state['DISK'] = self.disk_combo.get_model()[it][0]
        
        # Manual mode doesn't use these — clear them so they don't leak from state
        self.state.pop('SWAP_ENABLED', None)
        self.state.pop('USE_LUKS', None)
        self.state.pop('LUKS_PASS', None)
        self.state.pop('USE_LVM', None)