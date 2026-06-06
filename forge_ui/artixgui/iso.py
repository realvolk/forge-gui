#!/usr/bin/env python3
import subprocess
import os
from gi.repository import Gtk
from .base import BaseWindow

class ISOBuilderWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Build ISO")
        self.add_page("Boot Mode", self.create_bootmode_page())
        self.add_page("Configuration Method", self.create_config_page())
        self.add_page("Quick Profile", self.create_quickprofile_page())
        self.add_page("Manual Config", self.create_manual_page())
        self.add_page("Installer Mode", self.create_installer_page())
        self.add_page("Extra Packages", self.create_extras_page())
        self.add_page("Offline & Build", self.create_build_page())
        self.boot_mode = "live"
        self.config_method = "quick"
        self.profile_name = "Desktop"
        self.init = "openrc"
        self.kernel = "linux"
        self.offline = False
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

        # Init system
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.pack_start(init_label, False, False, 5)
        self.init_combo = Gtk.ComboBoxText()
        for init in ["openrc", "runit", "dinit", "s6"]:
            self.init_combo.append_text(init)
        self.init_combo.set_active(0)
        box.pack_start(self.init_combo, False, False, 0)

        # Kernel
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.pack_start(kernel_label, False, False, 5)
        self.kernel_combo = Gtk.ComboBoxText()
        for kernel in ["linux", "linux-zen", "linux-lts", "linux-hardened"]:
            self.kernel_combo.append_text(kernel)
        self.kernel_combo.set_active(0)
        box.pack_start(self.kernel_combo, False, False, 0)

        # Desktop (if building Live Desktop)
        de_label = Gtk.Label(label="Desktop environment (Live Desktop only):", xalign=0)
        box.pack_start(de_label, False, False, 5)
        self.de_combo = Gtk.ComboBoxText()
        for de in ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]:
            self.de_combo.append_text(de)
        self.de_combo.set_active(0)
        box.pack_start(self.de_combo, False, False, 0)

        return box

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
        box.pack_start(self.offline_check, False, False, 10)

        build_btn = Gtk.Button(label="Build ISO")
        build_btn.get_style_context().add_class("suggested-action")
        build_btn.connect("clicked", self.on_build_iso)
        box.pack_start(build_btn, False, False, 10)

        return box

    def on_build_iso(self, widget):
        # Collect all configuration
        self.boot_mode = "live" if self.bootmode_combo.get_active_text().startswith("Live") else "installer"
        self.config_method = self.config_combo.get_active_text()
        self.extra_packages = self.extra_entry.get_text().strip()
        self.offline = self.offline_check.get_active()

        if self.boot_mode == "live":
            if self.config_method.startswith("Quick Profile"):
                self.profile_name = self.profile_combo.get_active_text()
                # Quick profiles set their own state; we'll just pass the name
            elif self.config_method.startswith("Full Customization"):
                self.profile_name = "Custom"
                self.init = self.init_combo.get_active_text()
                self.kernel = self.kernel_combo.get_active_text()
                # Desktop will be handled by the installer's state collection
            else:  # Load Profile
                self.profile_name = "Loaded"
                # Profile loading will be done by the installer
        else:  # installer mode
            self.profile_name = "Installer"
            self.init = self.installer_init_combo.get_active_text()
            self.kernel = self.installer_kernel_combo.get_active_text()

        # Build the ISO using the Bash backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        iso_dir = f"{base_dir}/iso"

        # Create a temporary state file with the configuration
        state_file = "/tmp/artix-installer/state.conf"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            f.write(f'QUICK_PROFILE="{self.profile_name}"\n')
            f.write(f'INIT="{self.init}"\n')
            f.write(f'KERNEL_CHOICE="{self.kernel}"\n')
            f.write(f'ISO_EXTRA_PACKAGES="{self.extra_packages}"\n')
            if self.boot_mode == "live":
                f.write(f'WM_DE="{self.de_combo.get_active_text() if hasattr(self, "de_combo") else "kde"}"\n')
                f.write('X_STACK="xlibre"\n')
                f.write('DISPLAY_MANAGER="sddm"\n')
                f.write('NETWORK_STACK="networkmanager"\n')
                f.write('AUDIO_STACK="pipewire"\n')

        # Run the ISO build script
        cmd = ["bash", "-c", f"""
            source {iso_dir}/common.sh
            source {iso_dir}/build.sh
            export BASE_DIR="{base_dir}"
            export STATE_FILE="{state_file}"
            build_artix_iso "{self.profile_name}" "{self.init}" "{self.kernel}" {"yes" if self.offline else "no"} "{self.boot_mode}"
        """]

        from ..backends.gui import ProgressWindow
        progress = ProgressWindow(
            {"title": f"Building {self.boot_mode} ISO", "command": cmd},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()

        if result.get("result") == "success":
            dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                       message_format="ISO built successfully!\n\nCheck ~/artixforge-iso/")
            dialog.run()
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                       message_format="ISO build failed. Check logs.")
            dialog.run()
            dialog.destroy()
        Gtk.main_quit()

    def on_next(self, widget):
        # Dynamic navigation based on user choices
        if self.current_page == 0:  # Boot mode page
            self.boot_mode = "live" if self.bootmode_combo.get_active_text().startswith("Live") else "installer"
            if self.boot_mode == "live":
                self.stack.set_visible_child(self.pages[1])  # Config method page
                self.current_page = 1
            else:
                self.stack.set_visible_child(self.pages[4])  # Installer mode page
                self.current_page = 4
            self.update_nav_buttons()
        elif self.current_page == 1:  # Config method page
            self.config_method = self.config_combo.get_active_text()
            if self.config_method.startswith("Quick Profile"):
                self.stack.set_visible_child(self.pages[2])  # Quick profile page
                self.current_page = 2
            elif self.config_method.startswith("Full Customization"):
                self.stack.set_visible_child(self.pages[3])  # Manual config page
                self.current_page = 3
            else:  # Load Profile
                # Skip to extras page – profile will be loaded later
                self.stack.set_visible_child(self.pages[5])  # Extras page
                self.current_page = 5
            self.update_nav_buttons()
        elif self.current_page == 2 or self.current_page == 3:
            self.stack.set_visible_child(self.pages[5])  # Extras page
            self.current_page = 5
            self.update_nav_buttons()
        elif self.current_page == 4:
            self.stack.set_visible_child(self.pages[5])  # Extras page
            self.current_page = 5
            self.update_nav_buttons()
        elif self.current_page == 5:
            self.stack.set_visible_child(self.pages[6])  # Build page
            self.current_page = 6
            self.update_nav_buttons()
        else:
            self.start_installation()