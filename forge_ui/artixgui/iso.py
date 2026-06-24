#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
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
        self.iso_stage_file = "/tmp/artix-installer/iso-build-stage.conf"
        if os.path.exists(self.iso_stage_file):
            self.add_page("Resume ISO Build", self.create_resume_page())
    
    def create_resume_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Resume ISO Build</span>')
        box.append(label)
        desc = Gtk.Label()
        with open(self.iso_stage_file) as f:
            stage = f.read().strip()
        desc.set_text(f"A previous ISO build was interrupted at stage: {stage}\n\nClick Resume to continue from where it stopped, or Start Fresh to begin a new build.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        resume_btn = Gtk.Button(label="Resume")
        resume_btn.connect("clicked", lambda b: self.start_installation())
        box.append(resume_btn)
        fresh_btn = Gtk.Button(label="Start Fresh")
        fresh_btn.connect("clicked", self.on_fresh_build)
        box.append(fresh_btn)
        return box
    
    def on_fresh_build(self, widget):
        if os.path.exists(self.iso_stage_file):
            os.remove(self.iso_stage_file)
        self.stack.set_visible_child(self.pages[0])
        self.current_page = 0
        self.update_nav_buttons()

    def create_bootmode_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">ISO Type</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("What kind of ISO do you want to build?")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.bootmode_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Live Desktop – full graphical environment, installer available manually",
            "Installer – boots directly into ArtixForge installer"
        ]))
        box.append(self.bootmode_combo)
        return box

    def create_config_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Configuration Method</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("How would you like to configure the ISO?")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.config_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Quick Profile – use a preset",
            "Full Customization – choose every option",
            "Load Profile – from saved configuration file"
        ]))
        box.append(self.config_combo)
        return box

    def create_quickprofile_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Quick Profile</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Select a preset:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        profiles = ["Desktop", "Server", "Minimal", "Embedded", "Gaming", "Development", "Media", "Volk's Personal"]
        self.profile_combo = Gtk.DropDown.new(Gtk.StringList.new(profiles))
        box.append(self.profile_combo)
        return box

    def create_manual_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Manual Configuration</span>')
        box.append(label)
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.append(init_label)
        self.init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        box.append(self.init_combo)
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.append(kernel_label)
        self.kernel_combo = Gtk.DropDown.new(Gtk.StringList.new(["linux", "linux-zen", "linux-lts", "linux-hardened"]))
        box.append(self.kernel_combo)
        de_label = Gtk.Label(label="Desktop environment (Live Desktop only):", xalign=0)
        box.append(de_label)
        self.de_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
            "i3wm", "dwm", "vxwm", "icewm", "mango",
            "cinnamon", "budgie", "moksha", "cosmic", "none"
        ]))
        box.append(self.de_combo)
        return box

    def create_loadprofile_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Load Profile</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Enter path to saved profile file:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.profile_path_entry = Gtk.Entry()
        self.profile_path_entry.set_text("/etc/artixforge-profile.conf")
        box.append(self.profile_path_entry)
        browse_btn = Gtk.Button(label="Browse...")
        browse_btn.connect("clicked", self.on_browse_profile)
        box.append(browse_btn)
        return box

    def on_browse_profile(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Profile File", action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.OK)
        dialog.set_transient_for(self.window)
        dialog.show()
        dialog.connect("response", self._on_file_response)

    def _on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            file = dialog.get_file()
            if file:
                self.profile_path_entry.set_text(file.get_path())
        dialog.destroy()

    def create_installer_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Installer Mode Configuration</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("For installer ISO (boots directly into ArtixForge):")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.append(init_label)
        self.installer_init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        box.append(self.installer_init_combo)
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.append(kernel_label)
        self.installer_kernel_combo = Gtk.DropDown.new(Gtk.StringList.new(["linux", "linux-zen", "linux-lts", "linux-hardened"]))
        box.append(self.installer_kernel_combo)
        return box

    def create_extras_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Extra Packages</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Add additional packages to the ISO (space-separated):")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.extra_entry = Gtk.Entry()
        self.extra_entry.set_placeholder_text("e.g. firefox neovim kitty")
        box.append(self.extra_entry)
        return box

    def create_build_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Offline & Build</span>')
        box.append(label)
        self.offline_check = Gtk.CheckButton(label="Include all packages for offline installation (larger ISO)")
        self.offline_check.set_active(False)
        box.append(self.offline_check)
        output_label = Gtk.Label(label="Output directory:", xalign=0)
        box.append(output_label)
        self.output_entry = Gtk.Entry()
        self.output_entry.set_text(os.path.expanduser("~/ArtixForge-ISO"))
        box.append(self.output_entry)
        self.arch_repos_check = Gtk.CheckButton(label="Include Arch Linux repositories in the ISO")
        box.append(self.arch_repos_check)
        return box

    def create_target_config_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Target System Configuration</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Configure the system you will later install with this ISO.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        init_label = Gtk.Label(label="Init system:", xalign=0)
        box.append(init_label)
        self.target_init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        box.append(self.target_init_combo)
        kernel_label = Gtk.Label(label="Kernel:", xalign=0)
        box.append(kernel_label)
        self.target_kernel_combo = Gtk.DropDown.new(Gtk.StringList.new(["linux", "linux-zen", "linux-lts", "linux-hardened", "linux-cachyos-bore", "xanmod", "tkg"]))
        box.append(self.target_kernel_combo)
        de_label = Gtk.Label(label="Desktop environment:", xalign=0)
        box.append(de_label)
        self.target_de_combo = Gtk.DropDown.new(Gtk.StringList.new(["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]))
        box.append(self.target_de_combo)
        return box

    def _save_target_state(self):
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

    def _get_combo(self, combo, values):
        idx = combo.get_selected()
        return values[idx] if 0 <= idx < len(values) else values[0]

    def collect_state(self):
        self.boot_mode = "live" if self.bootmode_combo.get_selected() == 0 else "installer"
        self.config_method = self._get_combo(self.config_combo, ["Quick Profile", "Full Customization", "Load Profile"])
        self.extra_packages = self.extra_entry.get_text().strip()
        self.offline = "yes" if self.offline_check.get_active() else "no"

        if self.boot_mode == "live":
            if self.config_method == "Quick Profile":
                profiles = ["Desktop", "Server", "Minimal", "Embedded", "Gaming", "Development", "Media", "Volk's Personal"]
                self.profile_name = self._get_combo(self.profile_combo, profiles)
            elif self.config_method == "Full Customization":
                self.profile_name = "Custom"
                self.state['INIT'] = self._get_combo(self.init_combo, ["openrc", "runit", "dinit", "s6"])
                self.state['KERNEL_CHOICE'] = self._get_combo(self.kernel_combo, ["linux", "linux-zen", "linux-lts", "linux-hardened"])
                self.state['WM_DE'] = self._get_combo(self.de_combo, ["kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"])
            else:
                self.profile_name = "Loaded"
                self.state['PROFILE_FILE'] = self.profile_path_entry.get_text()
        else:
            self.profile_name = "Installer"
            self.state['INIT'] = self._get_combo(self.installer_init_combo, ["openrc", "runit", "dinit", "s6"])
            self.state['KERNEL_CHOICE'] = self._get_combo(self.installer_kernel_combo, ["linux", "linux-zen", "linux-lts", "linux-hardened"])
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
        self.state['ISO_ARCH_REPOS'] = "yes" if self.arch_repos_check.get_active() else "no"

        if self.offline == "yes":
            self.state['TARGET_INIT'] = self._get_combo(self.target_init_combo, ["openrc", "runit", "dinit", "s6"])
            self.state['TARGET_KERNEL'] = self._get_combo(self.target_kernel_combo, ["linux", "linux-zen", "linux-lts", "linux-hardened", "linux-cachyos-bore", "xanmod", "tkg"])
            self.state['TARGET_WM_DE'] = self._get_combo(self.target_de_combo, ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"])
            self._save_target_state()

    def start_installation(self):
        self.collect_state()
        self.save_state()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        install_script = os.path.join(base_dir, "install")
        self.window.hide()
        progress = ProgressWindow(
            {"title": f"Building {self.boot_mode} ISO", "command": [install_script, "--non-interactive"]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()
        if result.get("cancelled"):
            msg = "ISO build cancelled."
            mt = Gtk.MessageType.WARNING
        elif result.get("result") == "success":
            msg = "ISO built successfully!\n\nCheck ~/ArtixForge-ISO/"
            mt = Gtk.MessageType.INFO
        else:
            msg = "ISO build failed. Check logs."
            mt = Gtk.MessageType.ERROR
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True, message_type=mt, buttons=Gtk.ButtonsType.OK, text=msg)
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())

    def on_next(self, widget):
        if self.current_page == 0:
            self.boot_mode = "live" if self.bootmode_combo.get_selected() == 0 else "installer"
            if self.boot_mode == "live":
                self.stack.set_visible_child(self.pages[1])
                self.current_page = 1
            else:
                self.stack.set_visible_child(self.pages[5])
                self.current_page = 5
            self.update_nav_buttons()
        elif self.current_page == 1:
            self.config_method = self._get_combo(self.config_combo, ["Quick Profile", "Full Customization", "Load Profile"])
            if self.config_method == "Quick Profile":
                self.stack.set_visible_child(self.pages[2])
                self.current_page = 2
            elif self.config_method == "Full Customization":
                self.stack.set_visible_child(self.pages[3])
                self.current_page = 3
            else:
                self.stack.set_visible_child(self.pages[4])
                self.current_page = 4
            self.update_nav_buttons()
        elif self.current_page in (2, 3, 4):
            self.stack.set_visible_child(self.pages[6])
            self.current_page = 6
            self.update_nav_buttons()
        elif self.current_page == 5:
            self.stack.set_visible_child(self.pages[6])
            self.current_page = 6
            self.update_nav_buttons()
        elif self.current_page == 6:
            self.stack.set_visible_child(self.pages[7])
            self.current_page = 7
            self.update_nav_buttons()
        elif self.current_page == 7:
            if self.offline_check.get_active():
                self.stack.set_visible_child(self.pages[8])
                self.current_page = 8
            else:
                self.start_installation()
            self.update_nav_buttons()
        else:
            self.start_installation()