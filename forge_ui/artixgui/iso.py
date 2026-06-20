#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
import os
from gi.repository import Gtk
from .base import BaseWindow
from ..backends.gui import ProgressWindow

class ISOBuilderWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Build ISO")
        self.add_page("Boot Mode", self.create_bootmode_page())
        self.add_page("Configuration Method", self.create_config_page())
        self.add_page("Quick Profile", self.create_quickprofile_page())
        self.add_page("Manual Config", self.create_manual_page())
        self.add_page("Load Profile", self.create_loadprofile_page())
        self.add_page("Installer Mode", self.create_installer_page())
        self.add_page("Extra Packages", self.create_extras_page())
        self.add_page("Offline & Build", self.create_build_page())
        self.add_page("Target System Config", self.create_target_config_page())

        self.boot_mode = "live"
        self.config_method = "quick"
        self.profile_name = "Desktop"
        self.offline = "no"
        self.extra_packages = ""

    def create_bootmode_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">ISO Type</span>')
        box.pack_start(label, False, False, 0)
        desc = Gtk.Label()
        desc.set_text("What kind of ISO do you want to build?")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        self.bootmode_combo = Gtk.ComboBoxText()
        self.bootmode_combo.append_text("Live Desktop – full graphical environment, installer available manually")
        self.bootmode_combo.append_text("Installer – boots directly into ArtixForge installer")
        self.bootmode_combo.set_active(0)
        box.pack_start(self.bootmode_combo, False, False, 5)
        return box

    def create_config_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Configuration Method</span>')
        box.pack_start(label, False, False, 0)
        desc = Gtk.Label()
        desc.set_text("How would you like to configure the ISO?")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        self.config_combo = Gtk.ComboBoxText()
        self.config_combo.append_text("Quick Profile – use a preset")
        self.config_combo.append_text("Full Customization – choose every option")
        self.config_combo.append_text("Load Profile – from saved configuration file")
        self.config_combo.set_active(0)
        box.pack_start(self.config_combo, False, False, 5)
        return box

    def create_quickprofile_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Quick Profile</span>')
        box.pack_start(label, False, False, 0)
        desc = Gtk.Label()
        desc.set_text("Select a preset:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        self.profile_combo = Gtk.ComboBoxText()
        profiles = ["Desktop", "Server", "Minimal", "Embedded", "Gaming", "Development", "Media", "Volk's Personal"]
        for p in profiles:
            self.profile_combo.append_text(p)
        self.profile_combo.set_active(0)
        box.pack_start(self.profile_combo, False, False, 5)
        return box

    def create_manual_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Manual Configuration</span>')
        box.pack_start(label, False, False, 0)
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.pack_start(init_label, False, False, 5)
        self.init_combo = Gtk.ComboBoxText()
        for init in ["openrc", "runit", "dinit", "s6"]:
            self.init_combo.append_text(init)
        self.init_combo.set_active(0)
        box.pack_start(self.init_combo, False, False, 0)
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.pack_start(kernel_label, False, False, 5)
        self.kernel_combo = Gtk.ComboBoxText()
        for kernel in ["linux", "linux-zen", "linux-lts", "linux-hardened"]:
            self.kernel_combo.append_text(kernel)
        self.kernel_combo.set_active(0)
        box.pack_start(self.kernel_combo, False, False, 0)
        de_label = Gtk.Label(label="Desktop environment (Live Desktop only):", xalign=0)
        box.pack_start(de_label, False, False, 5)
        self.de_combo = Gtk.ComboBoxText()
        for de in ["kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]:
            self.de_combo.append_text(de)
        self.de_combo.set_active(0)
        box.pack_start(self.de_combo, False, False, 0)
        return box

    def create_loadprofile_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Load Profile</span>')
        box.pack_start(label, False, False, 0)
        desc = Gtk.Label()
        desc.set_text("Enter path to saved profile file:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        self.profile_path_entry = Gtk.Entry()
        self.profile_path_entry.set_text("/etc/artixforge-profile.conf")
        box.pack_start(self.profile_path_entry, False, False, 5)
        browse_btn = Gtk.Button(label="Browse...")
        browse_btn.connect("clicked", self.on_browse_profile)
        box.pack_start(browse_btn, False, False, 5)
        return box

    def on_browse_profile(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Profile File", parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            self.profile_path_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def create_installer_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Installer Mode Configuration</span>')
        box.pack_start(label, False, False, 0)
        desc = Gtk.Label()
        desc.set_text("For installer ISO (boots directly into ArtixForge):")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.pack_start(init_label, False, False, 5)
        self.installer_init_combo = Gtk.ComboBoxText()
        for init in ["openrc", "runit", "dinit", "s6"]:
            self.installer_init_combo.append_text(init)
        self.installer_init_combo.set_active(0)
        box.pack_start(self.installer_init_combo, False, False, 0)
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.pack_start(kernel_label, False, False, 5)
        self.installer_kernel_combo = Gtk.ComboBoxText()
        for kernel in ["linux", "linux-zen", "linux-lts", "linux-hardened"]:
            self.installer_kernel_combo.append_text(kernel)
        self.installer_kernel_combo.set_active(0)
        box.pack_start(self.installer_kernel_combo, False, False, 0)
        return box

    def create_extras_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Extra Packages</span>')
        box.pack_start(label, False, False, 0)
        desc = Gtk.Label()
        desc.set_text("Add additional packages to the ISO (space-separated):")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        self.extra_entry = Gtk.Entry()
        self.extra_entry.set_placeholder_text("e.g. firefox neovim kitty")
        box.pack_start(self.extra_entry, False, False, 5)
        return box

    def create_build_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Offline & Build</span>')
        box.pack_start(label, False, False, 0)
        self.offline_check = Gtk.CheckButton(label="Include all packages for offline installation (larger ISO)")
        self.offline_check.set_active(False)
        self.offline_check.connect("toggled", self._on_offline_toggled)
        box.pack_start(self.offline_check, False, False, 10)

        output_label = Gtk.Label(label="Output directory:", xalign=0)
        box.pack_start(output_label, False, False, 5)
        self.output_entry = Gtk.Entry()
        self.output_entry.set_text(os.path.expanduser("~/ArtixForge-ISO"))
        box.pack_start(self.output_entry, False, False, 0)

        # Store reference to target config page index for conditional navigation
        self._target_config_page_idx = 8  # index of "Target System Config" page
        return box

    def _on_offline_toggled(self, check):
        # Show/hide target config page when navigating
        pass

    def create_target_config_page(self):
        """Page to configure the installed system packages for offline ISO."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Target System Configuration</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Configure the system you will later install with this ISO.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 5)

        # Init
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.pack_start(init_label, False, False, 0)
        self.target_init_combo = Gtk.ComboBoxText()
        for init in ["openrc", "runit", "dinit", "s6"]:
            self.target_init_combo.append_text(init)
        self.target_init_combo.set_active(0)
        box.pack_start(self.target_init_combo, False, False, 0)

        # Kernel
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.pack_start(kernel_label, False, False, 0)
        self.target_kernel_combo = Gtk.ComboBoxText()
        for k in ["linux", "linux-zen", "linux-lts", "linux-hardened", "linux-cachyos-bore", "xanmod", "tkg"]:
            self.target_kernel_combo.append_text(k)
        self.target_kernel_combo.set_active(0)
        box.pack_start(self.target_kernel_combo, False, False, 0)

        # Desktop
        de_label = Gtk.Label(label="Desktop environment:", xalign=0)
        box.pack_start(de_label, False, False, 0)
        self.target_de_combo = Gtk.ComboBoxText()
        for de in ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]:
            self.target_de_combo.append_text(de)
        self.target_de_combo.set_active(0)
        box.pack_start(self.target_de_combo, False, False, 0)

        return box

    def _save_target_state(self):
        """Write /tmp/artix-installer/iso-target-state.conf"""
        if self.offline != "yes":
            return
        target_state_file = "/tmp/artix-installer/iso-target-state.conf"
        try:
            os.makedirs(os.path.dirname(target_state_file), exist_ok=True)
            with open(target_state_file, 'w') as f:
                f.write(f'INIT="{self.state.get("TARGET_INIT", "openrc")}"\n')
                f.write(f'KERNEL_CHOICE="{self.state.get("TARGET_KERNEL", "linux")}"\n')
                f.write(f'WM_DE="{self.state.get("TARGET_WM_DE", "kde")}"\n')
        except Exception:
            pass

    def collect_state(self):
        self.boot_mode = "live" if self.bootmode_combo.get_active_text().startswith("Live") else "installer"
        self.config_method = self.config_combo.get_active_text()
        self.extra_packages = self.extra_entry.get_text().strip()
        self.offline = "yes" if self.offline_check.get_active() else "no"

        if self.boot_mode == "live":
            if self.config_method.startswith("Quick Profile"):
                self.profile_name = self.profile_combo.get_active_text()
            elif self.config_method.startswith("Full Customization"):
                self.profile_name = "Custom"
                self.state['INIT'] = self.init_combo.get_active_text()
                self.state['KERNEL_CHOICE'] = self.kernel_combo.get_active_text()
                self.state['WM_DE'] = self.de_combo.get_active_text()
            else:  # Load Profile
                self.profile_name = "Loaded"
                self.state['PROFILE_FILE'] = self.profile_path_entry.get_text()
        else:
            self.profile_name = "Installer"
            self.state['INIT'] = self.installer_init_combo.get_active_text()
            self.state['KERNEL_CHOICE'] = self.installer_kernel_combo.get_active_text()
            self.state['WM_DE'] = "none"
            self.state['DISPLAY_MANAGER'] = "none"
            self.state['X_STACK'] = "none"
            self.state['AUDIO_STACK'] = "none"

        self.state['QUICK_PROFILE'] = self.profile_name
        self.state['ISO_EXTRA_PACKAGES'] = self.extra_packages
        self.state['ISO_BOOT_MODE'] = self.boot_mode
        self.state['MODE'] = 'iso'
        self.state['GUI_MODE'] = 'yes'
        self.state['ALLOW_OFFLINE'] = self.offline
        self.state['ISO_OUTPUT_DIR'] = self.output_entry.get_text()

        # Target system config for offline
        if self.offline == "yes" and hasattr(self, 'target_init_combo'):
            self.state['TARGET_INIT'] = self.target_init_combo.get_active_text()
            self.state['TARGET_KERNEL'] = self.target_kernel_combo.get_active_text()
            self.state['TARGET_WM_DE'] = self.target_de_combo.get_active_text()
            self._save_target_state()

    def start_installation(self):
        self.collect_state()
        self.save_state()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        install_script = os.path.join(base_dir, "..", "install")

        self.window.hide()
        progress = ProgressWindow(
            {"title": f"Building {self.boot_mode} ISO", "command": ["sudo", install_script, "--non-interactive"]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()

        if result.get("cancelled"):
            dialog = Gtk.MessageDialog(parent=None, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                                       message_format="ISO build cancelled.")
        elif result.get("result") == "success":
            dialog = Gtk.MessageDialog(parent=None, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                       message_format="ISO built successfully!\n\nCheck ~/ArtixForge-ISO/")
        else:
            dialog = Gtk.MessageDialog(parent=None, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                       message_format="ISO build failed. Check logs.")
        dialog.run()
        dialog.destroy()
        Gtk.main_quit()

    def on_next(self, widget):
        if self.current_page == 0:
            self.boot_mode = "live" if self.bootmode_combo.get_active_text().startswith("Live") else "installer"
            if self.boot_mode == "live":
                self.stack.set_visible_child(self.pages[1])
                self.current_page = 1
            else:
                self.stack.set_visible_child(self.pages[5])  # Installer Mode page
                self.current_page = 5
            self.update_nav_buttons()
        elif self.current_page == 1:
            self.config_method = self.config_combo.get_active_text()
            if self.config_method.startswith("Quick Profile"):
                self.stack.set_visible_child(self.pages[2])
                self.current_page = 2
            elif self.config_method.startswith("Full Customization"):
                self.stack.set_visible_child(self.pages[3])
                self.current_page = 3
            else:  # Load Profile
                self.stack.set_visible_child(self.pages[4])
                self.current_page = 4
            self.update_nav_buttons()
        elif self.current_page in (2, 3, 4):
            # After configuration, go to extras
            self.stack.set_visible_child(self.pages[6])  # Extra Packages
            self.current_page = 6
            self.update_nav_buttons()
        elif self.current_page == 5:
            # Installer mode: go to extras
            self.stack.set_visible_child(self.pages[6])
            self.current_page = 6
            self.update_nav_buttons()
        elif self.current_page == 6:
            # From extras, go to offline & build
            self.stack.set_visible_child(self.pages[7])
            self.current_page = 7
            self.update_nav_buttons()
        elif self.current_page == 7:
            # If offline is checked, show target config page
            if self.offline_check.get_active():
                self.stack.set_visible_child(self.pages[8])
                self.current_page = 8
            else:
                self.start_installation()
            self.update_nav_buttons()
        else:
            self.start_installation()