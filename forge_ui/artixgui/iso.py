#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import os
from gi.repository import Gtk, Adw
from .base import InstallerApp


class ISOWizard:
    def __init__(self, app: InstallerApp):
        self.app = app
        self.iso_stage_file = "/tmp/artix-installer/iso-build-stage.conf"
        self.boot_mode = "live"
        self.config_method = "quick"
        self.profile_name = "Desktop"
        self.offline = "no"
        self.extra_packages = ""

    def push_pages(self):
        nav = self.app.nav_view
        if os.path.exists(self.iso_stage_file):
            nav.push(Adw.NavigationPage(child=self._create_resume_page(), title="Resume ISO Build"))
        nav.push(Adw.NavigationPage(child=self._create_bootmode_page(), title="ISO Type"))
        nav.push(Adw.NavigationPage(child=self._create_config_page(), title="Configuration Method"))
        nav.push(Adw.NavigationPage(child=self._create_quickprofile_page(), title="Quick Profile"))
        nav.push(Adw.NavigationPage(child=self._create_manual_page(), title="Manual Configuration"))
        nav.push(Adw.NavigationPage(child=self._create_loadprofile_page(), title="Load Profile"))
        nav.push(Adw.NavigationPage(child=self._create_installer_page(), title="Installer Mode"))
        nav.push(Adw.NavigationPage(child=self._create_extras_page(), title="Extra Packages"))
        nav.push(Adw.NavigationPage(child=self._create_build_page(), title="Offline & Build"))
        nav.push(Adw.NavigationPage(child=self._create_target_config_page(), title="Target System Config"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="Build ISO"))

    def _create_resume_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Resume ISO Build")
        desc = Gtk.Label()
        with open(self.iso_stage_file) as f:
            stage = f.read().strip()
        desc.set_text(f"A previous ISO build was interrupted at stage: {stage}\n\nClick Resume to continue, or Start Fresh to begin a new build.")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        group.add(desc)

        btn_box = Gtk.Box(spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)
        resume_btn = Gtk.Button(label="Resume")
        resume_btn.add_css_class("suggested-action")
        resume_btn.connect("clicked", lambda b: self._on_install())
        btn_box.append(resume_btn)
        fresh_btn = Gtk.Button(label="Start Fresh")
        fresh_btn.connect("clicked", self._on_fresh_build)
        btn_box.append(fresh_btn)
        group.add(btn_box)

        page.add(group)
        return page

    def _on_fresh_build(self, widget):
        if os.path.exists(self.iso_stage_file):
            os.remove(self.iso_stage_file)
        self.app.nav_view.pop_to_tag("ISO Type")

    def _create_bootmode_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="ISO Type")
        self.app.bootmode_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Live Desktop – full graphical environment, installer available manually",
            "Installer – boots directly into ArtixForge installer"
        ]))
        row = Adw.ActionRow(title="Boot Mode", subtitle="What kind of ISO do you want to build?")
        row.add_suffix(self.app.bootmode_combo)
        group.add(row)
        page.add(group)
        return page

    def _create_config_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Configuration Method")
        self.app.config_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Quick Profile – use a preset",
            "Full Customization – choose every option",
            "Load Profile – from saved configuration file"
        ]))
        row = Adw.ActionRow(title="Method", subtitle="How would you like to configure the ISO?")
        row.add_suffix(self.app.config_combo)
        group.add(row)
        page.add(group)
        return page

    def _create_quickprofile_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Quick Profile")
        profiles = ["Desktop", "Server", "Minimal", "Embedded", "Gaming", "Development", "Media", "Volk's Personal"]
        self.app.profile_combo = Gtk.DropDown.new(Gtk.StringList.new(profiles))
        row = Adw.ActionRow(title="Profile", subtitle="Select a preset")
        row.add_suffix(self.app.profile_combo)
        group.add(row)
        page.add(group)
        return page

    def _create_manual_page(self):
        page = Adw.PreferencesPage()

        init_group = Adw.PreferencesGroup(title="Init System")
        self.app.init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        init_row = Adw.ActionRow(title="Init system")
        init_row.add_suffix(self.app.init_combo)
        init_group.add(init_row)

        kernel_group = Adw.PreferencesGroup(title="Kernel")
        self.app.kernel_combo = Gtk.DropDown.new(Gtk.StringList.new(["linux", "linux-zen", "linux-lts", "linux-hardened"]))
        kernel_row = Adw.ActionRow(title="Kernel")
        kernel_row.add_suffix(self.app.kernel_combo)
        kernel_group.add(kernel_row)

        de_group = Adw.PreferencesGroup(title="Desktop Environment (Live Desktop only)")
        self.app.de_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
            "i3wm", "dwm", "vxwm", "icewm", "mango",
            "cinnamon", "budgie", "moksha", "cosmic", "none"
        ]))
        de_row = Adw.ActionRow(title="Desktop environment")
        de_row.add_suffix(self.app.de_combo)
        de_group.add(de_row)

        page.add(init_group)
        page.add(kernel_group)
        page.add(de_group)
        return page

    def _create_loadprofile_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Load Profile")
        self.app.profile_path_entry = Gtk.Entry()
        self.app.profile_path_entry.set_text("/etc/artixforge-profile.conf")
        row = Adw.ActionRow(title="Profile Path", subtitle="Enter path to saved profile file")
        row.add_suffix(self.app.profile_path_entry)
        group.add(row)

        browse_btn = Gtk.Button(label="Browse...")
        browse_btn.connect("clicked", self._on_browse_profile)
        group.add(browse_btn)

        page.add(group)
        return page

    def _on_browse_profile(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Profile File", action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.OK)
        dialog.set_transient_for(self.app.window)
        dialog.show()
        dialog.connect("response", self._on_file_response)

    def _on_file_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            file = dialog.get_file()
            if file:
                self.app.profile_path_entry.set_text(file.get_path())
        dialog.destroy()

    def _create_installer_page(self):
        page = Adw.PreferencesPage()
        init_group = Adw.PreferencesGroup(title="Init System")
        self.app.installer_init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        init_row = Adw.ActionRow(title="Init system")
        init_row.add_suffix(self.app.installer_init_combo)
        init_group.add(init_row)

        kernel_group = Adw.PreferencesGroup(title="Kernel")
        self.app.installer_kernel_combo = Gtk.DropDown.new(Gtk.StringList.new(["linux", "linux-zen", "linux-lts", "linux-hardened"]))
        kernel_row = Adw.ActionRow(title="Kernel")
        kernel_row.add_suffix(self.app.installer_kernel_combo)
        kernel_group.add(kernel_row)

        page.add(init_group)
        page.add(kernel_group)
        return page

    def _create_extras_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Extra Packages")
        self.app.extra_entry = Gtk.Entry()
        self.app.extra_entry.set_placeholder_text("e.g. firefox neovim kitty")
        row = Adw.ActionRow(title="Additional packages", subtitle="Space-separated list")
        row.add_suffix(self.app.extra_entry)
        group.add(row)
        page.add(group)
        return page

    def _create_build_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Offline & Build")

        self.app.offline_switch = Gtk.Switch()
        off_row = Adw.ActionRow(title="Offline installation", subtitle="Include all packages for offline installation (larger ISO)")
        off_row.add_suffix(self.app.offline_switch)
        group.add(off_row)

        self.app.output_entry = Gtk.Entry()
        self.app.output_entry.set_text(os.path.expanduser("~/ArtixForge-ISO"))
        out_row = Adw.ActionRow(title="Output directory", subtitle="Where to save the ISO")
        out_row.add_suffix(self.app.output_entry)
        group.add(out_row)

        self.app.iso_arch_repos_switch = Gtk.Switch()
        arch_row = Adw.ActionRow(title="Include Arch Linux repositories", subtitle="Add Arch repos to the ISO")
        arch_row.add_suffix(self.app.iso_arch_repos_switch)
        group.add(arch_row)

        page.add(group)
        return page

    def _create_target_config_page(self):
        page = Adw.PreferencesPage()
        init_group = Adw.PreferencesGroup(title="Init System")
        self.app.target_init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        init_row = Adw.ActionRow(title="Init system")
        init_row.add_suffix(self.app.target_init_combo)
        init_group.add(init_row)

        kernel_group = Adw.PreferencesGroup(title="Kernel")
        self.app.target_kernel_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "linux", "linux-zen", "linux-lts", "linux-hardened", "linux-cachyos-bore", "xanmod", "tkg"
        ]))
        kernel_row = Adw.ActionRow(title="Kernel")
        kernel_row.add_suffix(self.app.target_kernel_combo)
        kernel_group.add(kernel_row)

        de_group = Adw.PreferencesGroup(title="Desktop Environment")
        self.app.target_de_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
            "i3wm", "dwm", "vxwm", "icewm", "mango", "none"
        ]))
        de_row = Adw.ActionRow(title="Desktop environment")
        de_row.add_suffix(self.app.target_de_combo)
        de_group.add(de_row)

        page.add(init_group)
        page.add(kernel_group)
        page.add(de_group)
        return page

    def _save_target_state(self):
        if self.offline != "yes":
            return
        target_state_file = "/tmp/artix-installer/iso-target-state.conf"
        try:
            os.makedirs(os.path.dirname(target_state_file), exist_ok=True)
            with open(target_state_file, 'w') as f:
                f.write(f'INIT="{self.app.state.get("TARGET_INIT", "openrc")}"\n')
                f.write(f'KERNEL_CHOICE="{self.app.state.get("TARGET_KERNEL", "linux")}"\n')
                f.write(f'WM_DE="{self.app.state.get("TARGET_WM_DE", "kde")}"\n')
        except Exception:
            pass

    def _get_combo(self, combo, values):
        idx = combo.get_selected()
        return values[idx] if 0 <= idx < len(values) else values[0]

    def _update_summary(self):
        self._collect_state()
        text = "ISO Build Summary:\n\n"
        for key, value in sorted(self.app.state.items()):
            if key not in ['LUKS_PASS', 'USER_PASS', 'ROOT_PASS']:
                text += f"{key}: {value}\n"
        self.app.summary_text.get_buffer().set_text(text)

    def _collect_state(self):
        self.boot_mode = "live" if self.app.bootmode_combo.get_selected() == 0 else "installer"
        self.config_method = self._get_combo(self.app.config_combo, ["Quick Profile", "Full Customization", "Load Profile"])
        self.extra_packages = self.app.extra_entry.get_text().strip() if hasattr(self.app, 'extra_entry') else ""
        self.offline = "yes" if hasattr(self.app, 'offline_switch') and self.app.offline_switch.get_active() else "no"

        if self.boot_mode == "live":
            if self.config_method == "Quick Profile":
                profiles = ["Desktop", "Server", "Minimal", "Embedded", "Gaming", "Development", "Media", "Volk's Personal"]
                self.profile_name = self._get_combo(self.app.profile_combo, profiles)
            elif self.config_method == "Full Customization":
                self.profile_name = "Custom"
                self.app.state['INIT'] = self._get_combo(self.app.init_combo, ["openrc", "runit", "dinit", "s6"])
                self.app.state['KERNEL_CHOICE'] = self._get_combo(self.app.kernel_combo, ["linux", "linux-zen", "linux-lts", "linux-hardened"])
                self.app.state['WM_DE'] = self._get_combo(self.app.de_combo, [
                    "kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
                    "i3wm", "dwm", "vxwm", "icewm", "mango", "cinnamon", "budgie", "moksha", "cosmic", "none"
                ])
            else:
                self.profile_name = "Loaded"
                self.app.state['PROFILE_FILE'] = self.app.profile_path_entry.get_text() if hasattr(self.app, 'profile_path_entry') else ""
        else:
            self.profile_name = "Installer"
            self.app.state['INIT'] = self._get_combo(self.app.installer_init_combo, ["openrc", "runit", "dinit", "s6"])
            self.app.state['KERNEL_CHOICE'] = self._get_combo(self.app.installer_kernel_combo, ["linux", "linux-zen", "linux-lts", "linux-hardened"])
            self.app.state['WM_DE'] = "none"
            self.app.state['DISPLAY_MANAGER'] = "none"
            self.app.state['X_STACK'] = "none"
            self.app.state['AUDIO_STACK'] = "none"

        self.app.state['QUICK_PROFILE'] = self.profile_name
        self.app.state['ISO_EXTRA_PACKAGES'] = self.extra_packages
        self.app.state['ISO_BOOT_MODE'] = self.boot_mode
        self.app.state['MODE'] = 'iso'
        self.app.state['GUI_MODE'] = 'yes'
        self.app.state['ALLOW_OFFLINE'] = self.offline
        if hasattr(self.app, 'output_entry'):
            self.app.state['ISO_OUTPUT_DIR'] = self.app.output_entry.get_text()
        if hasattr(self.app, 'iso_arch_repos_switch'):
            self.app.state['ISO_ARCH_REPOS'] = "yes" if self.app.iso_arch_repos_switch.get_active() else "no"

        if self.offline == "yes":
            self.app.state['TARGET_INIT'] = self._get_combo(self.app.target_init_combo, ["openrc", "runit", "dinit", "s6"])
            self.app.state['TARGET_KERNEL'] = self._get_combo(self.app.target_kernel_combo, [
                "linux", "linux-zen", "linux-lts", "linux-hardened", "linux-cachyos-bore", "xanmod", "tkg"
            ])
            self.app.state['TARGET_WM_DE'] = self._get_combo(self.app.target_de_combo, [
                "kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
                "i3wm", "dwm", "vxwm", "icewm", "mango", "none"
            ])
            self._save_target_state()

    def _on_install(self):
        self._collect_state()
        self.app.save_state()
        self.app.start_installation("Build ISO")