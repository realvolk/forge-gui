#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import subprocess
from gi.repository import Gtk, Adw
from .base import InstallerApp


class ManualWizard:
    def __init__(self, app: InstallerApp):
        self.app = app

    def push_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self.app.create_welcome_page(), title="Welcome"))
        nav.push(Adw.NavigationPage(child=self.app.create_theme_page(), title="Theme"))
        nav.push(Adw.NavigationPage(child=self._create_manual_disk_page(), title="Manual Partitioning"))
        nav.push(Adw.NavigationPage(child=self.app.create_filesystem_page(), title="Filesystem"))
        nav.push(Adw.NavigationPage(child=self.app.create_bootloader_page(), title="Bootloader"))
        nav.push(Adw.NavigationPage(child=self.app.create_kernel_page(), title="Kernel"))
        nav.push(Adw.NavigationPage(child=self.app.create_init_page(), title="Init System"))
        nav.push(Adw.NavigationPage(child=self.app.create_desktop_page(), title="Desktop"))
        nav.push(Adw.NavigationPage(child=self.app.create_network_audio_page(), title="Network & Audio"))
        nav.push(Adw.NavigationPage(child=self.app.create_extras_page(), title="Shell & Extras"))
        nav.push(Adw.NavigationPage(child=self.app.create_users_page(), title="Users"))
        nav.push(Adw.NavigationPage(child=self.app.create_privilege_page(), title="Privilege & Power"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="Summary"))

    def _create_manual_disk_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Manual Partitioning")

        desc = Gtk.Label()
        desc.set_text(
            "You will partition the disk yourself using tools like cfdisk or fdisk.\n\n"
            "After partitioning, the installer will continue automatically.\n\n"
            "Select the disk you want to partition:"
        )
        desc.set_wrap(True)
        desc.set_margin_bottom(10)
        group.add(desc)

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
        self.app.disk_combo = Gtk.DropDown.new(disk_list)
        disk_row = Adw.ActionRow(title="Disk", subtitle="Select target drive")
        disk_row.add_suffix(self.app.disk_combo)
        group.add(disk_row)

        reminder = Gtk.Label()
        reminder.set_text(
            "\nReminder: If you want swap, LUKS encryption, or LVM, "
            "you must set them up manually before continuing."
        )
        reminder.set_wrap(True)
        reminder.set_margin_top(10)
        group.add(reminder)

        page.add(group)
        return page

    def _update_summary(self):
        self.app.collect_state_common()
        if hasattr(self.app, 'disk_combo'):
            model = self.app.disk_combo.get_model()
            idx = self.app.disk_combo.get_selected()
            if model and 0 <= idx < model.get_n_items():
                self.app.state['DISK'] = model.get_string(idx)
        self.app.state.pop('SWAP_ENABLED', None)
        self.app.state.pop('USE_LUKS', None)
        self.app.state.pop('LUKS_PASS', None)
        self.app.state.pop('USE_LVM', None)

        text = "Installation Summary:\n\n"
        for key, value in sorted(self.app.state.items()):
            if key not in ['LUKS_PASS', 'USER_PASS', 'ROOT_PASS']:
                text += f"{key}: {value}\n"
        self.app.summary_text.get_buffer().set_text(text)

    def _on_install(self):
        self._update_summary()
        self.app.state['MODE'] = 'manual'
        self.app.state['GUI_MODE'] = 'yes'
        self.app.start_installation("Manual Installation")