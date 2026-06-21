#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import subprocess
from gi.repository import Gtk
from .automatic import AutomaticWindow

class ManualWindow(AutomaticWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state)
        self.window.set_title("Manual Installation")
        self.stack.remove(self.pages[2])
        self.pages[2] = self.create_manual_disk_page()
        self.stack.add_titled(self.pages[2], "Manual Disk", "Manual Disk")
        self.stack.set_visible_child(self.pages[0])

    def create_manual_disk_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Manual Partitioning</span>')
        box.append(label)

        desc = Gtk.Label()
        desc.set_text("You will partition the disk yourself using tools like cfdisk or fdisk.\n\nAfter partitioning, the installer will continue automatically.\n\nSelect the disk you want to partition:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)

        disk_list = Gtk.StringList.new([])
        result = subprocess.run(['lsblk', '-dpno', 'NAME,SIZE,MODEL', '-e', '7'],
                               capture_output=True, text=True)
        disk_names = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                name = line.split(' ', 1)[0]
                if '/dev/loop' in name or '/dev/sr' in name:
                    continue
                disk_names.append(name)
        if disk_names:
            disk_list = Gtk.StringList.new(disk_names)
        self.disk_combo = Gtk.DropDown.new(disk_list)
        box.append(self.disk_combo)

        reminder = Gtk.Label()
        reminder.set_text("\nReminder: If you want swap, LUKS encryption, or LVM,\nyou must set them up manually before continuing.")
        reminder.set_justify(Gtk.Justification.CENTER)
        box.append(reminder)

        return box

    def collect_state(self):
        if not self.collect_state_common():
            return
        self.state['MODE'] = 'manual'

        if hasattr(self, 'disk_combo'):
            idx = self.disk_combo.get_selected()
            model = self.disk_combo.get_model()
            if 0 <= idx < model.get_n_items():
                self.state['DISK'] = model.get_string(idx)

        self.state.pop('SWAP_ENABLED', None)
        self.state.pop('USE_LUKS', None)
        self.state.pop('LUKS_PASS', None)
        self.state.pop('USE_LVM', None)