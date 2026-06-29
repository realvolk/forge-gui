#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import subprocess
from gi.repository import Gtk, Adw, GLib
from .base import InstallerApp


class InstallationWizard:
    def __init__(self, app: InstallerApp):
        self.app = app

    def push_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self.app.create_welcome_page(), title="Welcome"))
        nav.push(Adw.NavigationPage(child=self.app.create_theme_page(), title="Theme"))
        nav.push(Adw.NavigationPage(child=self._create_disk_page(), title="Disk & Partitioning"))
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

    def _create_disk_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Target Disk")

        disk_list = Gtk.StringList.new([])
        result = subprocess.run(['lsblk', '-dpno', 'NAME,SIZE,MODEL', '-e', '7'],
                                capture_output=True, text=True)
        disk_names = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                name = parts[0]
                if '/dev/loop' in name or '/dev/sr' in name:
                    continue
                disk_names.append(name)
        if disk_names:
            disk_list = Gtk.StringList.new(disk_names)
        self.app.disk_combo = Gtk.DropDown.new(disk_list)
        disk_row = Adw.ActionRow(title="Disk", subtitle="Select target drive")
        disk_row.add_suffix(self.app.disk_combo)
        group.add(disk_row)

        self.app.whole_disk_switch = Gtk.Switch()
        self.app.whole_disk_switch.set_active(True)
        whole_row = Adw.ActionRow(title="Use entire disk", subtitle="Auto-partition with ESP and root")
        whole_row.add_suffix(self.app.whole_disk_switch)
        group.add(whole_row)

        self.app.auto_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        self.app.swap_switch = Gtk.Switch()
        swap_row = Adw.ActionRow(title="Create swap partition")
        swap_row.add_suffix(self.app.swap_switch)
        self.app.auto_box.append(swap_row)

        self.app.luks_switch = Gtk.Switch()
        luks_row = Adw.ActionRow(title="Enable LUKS encryption")
        luks_row.add_suffix(self.app.luks_switch)
        self.app.auto_box.append(luks_row)

        self.app.luks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.app.luks_pass_entry = Gtk.PasswordEntry()
        self.app.luks_pass_entry.set_show_peek_icon(False)
        luks_pass_row = Adw.ActionRow(title="LUKS Passphrase")
        luks_pass_row.add_suffix(self.app.luks_pass_entry)
        self.app.luks_box.append(luks_pass_row)

        self.app.luks_confirm_entry = Gtk.PasswordEntry()
        self.app.luks_confirm_entry.set_show_peek_icon(False)
        luks_confirm_row = Adw.ActionRow(title="Confirm Passphrase")
        luks_confirm_row.add_suffix(self.app.luks_confirm_entry)
        self.app.luks_box.append(luks_confirm_row)

        self.app.keyfile_switch = Gtk.Switch()
        keyfile_row = Adw.ActionRow(title="Use keyfile (avoids double password prompt)")
        keyfile_row.add_suffix(self.app.keyfile_switch)
        self.app.luks_box.append(keyfile_row)
        self.app.luks_box.set_visible(False)
        self.app.auto_box.append(self.app.luks_box)

        self.app.lvm_switch = Gtk.Switch()
        lvm_row = Adw.ActionRow(title="Enable LVM")
        lvm_row.add_suffix(self.app.lvm_switch)
        self.app.auto_box.append(lvm_row)

        group.add(self.app.auto_box)

        self.app.manual_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        manual_label = Gtk.Label()
        manual_label.set_text(
            "You will partition the disk yourself using tools like cfdisk or fdisk.\n"
            "Create an EFI partition (≥512 MiB) and a root partition.\n"
            "If you want swap, LUKS, or LVM, set them up manually."
        )
        manual_label.set_wrap(True)
        manual_label.set_margin_bottom(10)
        self.app.manual_box.append(manual_label)
        self.app.manual_box.set_visible(False)
        group.add(self.app.manual_box)

        def on_whole_toggled(switch, state):
            self.app.auto_box.set_visible(state)
            self.app.manual_box.set_visible(not state)
        self.app.whole_disk_switch.connect("state-set", on_whole_toggled)

        def on_luks_toggled(switch, state):
            self.app.luks_box.set_visible(state)
        self.app.luks_switch.connect("state-set", on_luks_toggled)

        page.add(group)
        return page

    def _update_summary(self):
        self.app.collect_state_common()
        if hasattr(self.app, 'disk_combo'):
            model = self.app.disk_combo.get_model()
            idx = self.app.disk_combo.get_selected()
            if model and 0 <= idx < model.get_n_items():
                self.app.state['DISK'] = model.get_string(idx)
        if hasattr(self.app, 'whole_disk_switch'):
            if not self.app.whole_disk_switch.get_active():
                self.app.state['EFI_PART'] = ""  # user will partition manually
                self.app.state['ROOT_PART'] = ""
        if hasattr(self.app, 'swap_switch'):
            self.app.state['SWAP_ENABLED'] = "yes" if self.app.swap_switch.get_active() else "no"
        if hasattr(self.app, 'luks_switch'):
            self.app.state['USE_LUKS'] = "yes" if self.app.luks_switch.get_active() else "no"
            if self.app.luks_switch.get_active() and hasattr(self.app, 'luks_pass_entry'):
                self.app.state['LUKS_PASS'] = self.app.luks_pass_entry.get_text()
            if hasattr(self.app, 'keyfile_switch'):
                self.app.state['LUKS_KEYFILE'] = "yes" if self.app.keyfile_switch.get_active() else "no"
        if hasattr(self.app, 'lvm_switch'):
            self.app.state['USE_LVM'] = "yes" if self.app.lvm_switch.get_active() else "no"

        text = "Installation Summary:\n\n"
        for key, value in sorted(self.app.state.items()):
            if key not in ['LUKS_PASS', 'USER_PASS', 'ROOT_PASS']:
                text += f"{key}: {value}\n"
        self.app.summary_text.get_buffer().set_text(text)

    def _on_install(self):
        self._update_summary()
        self.app.state['MODE'] = 'auto'
        self.app.state['GUI_MODE'] = 'yes'
        self.app.start_installation("Installation")