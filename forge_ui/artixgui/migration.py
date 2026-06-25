#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import os
import subprocess
from gi.repository import Gtk, Adw
from .base import InstallerApp


class MigrationWizard:
    def __init__(self, app: InstallerApp):
        self.app = app
        self.migration_stage_file = "/tmp/artix-installer/migration-stage.conf"
        self.migration_type = None
        self._detect_current_system()

    def _detect_current_system(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        scripts_dir = os.path.join(base_dir, "..", "scripts")
        recovery_dir = os.path.join(scripts_dir, "recovery")
        script = f"""
export STATE_FILE="/tmp/artix-installer/state.conf"
source "{scripts_dir}/common.sh"
source "{scripts_dir}/state.sh"
source "{recovery_dir}/core.sh"
source "{recovery_dir}/detect.sh"
detect_init
detect_desktop
echo "INIT=$(state_get INIT openrc)"
echo "WM_DE=$(state_get WM_DE none)"
"""
        try:
            result = subprocess.run(["sudo", "bash", "-c", script], capture_output=True, text=True, timeout=30)
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, val = line.split('=', 1)
                    if key == "INIT":
                        self.app.state['DETECTED_INIT'] = val
                    elif key == "WM_DE":
                        self.app.state['DETECTED_DE'] = val
        except Exception:
            pass

    def push_pages(self):
        nav = self.app.nav_view

        if os.path.exists(self.migration_stage_file):
            nav.push(Adw.NavigationPage(child=self._create_resume_page(), title="Resume Migration"))

        nav.push(Adw.NavigationPage(child=self._create_type_page(), title="Migration Type"))

    def _create_resume_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Resume Migration")
        desc = Gtk.Label()
        with open(self.migration_stage_file) as f:
            stage = f.read().strip()
        desc.set_text(f"A previous migration was interrupted at stage: {stage}\n\nClick Resume to continue, or Start Fresh to begin a new migration.")
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
        fresh_btn.connect("clicked", self._on_fresh_migration)
        btn_box.append(fresh_btn)
        group.add(btn_box)

        page.add(group)
        return page

    def _on_fresh_migration(self, widget):
        if os.path.exists(self.migration_stage_file):
            os.remove(self.migration_stage_file)
        self.app.nav_view.pop()

    def _create_type_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="System Migration")

        detected = ""
        if self.app.state.get('DETECTED_INIT'):
            detected += f"Detected init: {self.app.state['DETECTED_INIT']}\n"
        if self.app.state.get('DETECTED_DE'):
            detected += f"Detected desktop: {self.app.state['DETECTED_DE']}"
        if detected:
            det_label = Gtk.Label(label=detected.strip())
            det_label.set_margin_bottom(10)
            group.add(det_label)

        self.app.type_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Init System (openrc ↔ runit ↔ dinit ↔ s6 ↔ systemd)",
            "Desktop Environment (KDE ↔ XFCE ↔ Sway etc.)",
            "Arch Linux → Artix (EXPERIMENTAL)"
        ]))
        row = Adw.ActionRow(title="Migration Type", subtitle="Choose what you want to migrate")
        row.add_suffix(self.app.type_combo)
        group.add(row)

        next_btn = Gtk.Button(label="Continue")
        next_btn.add_css_class("suggested-action")
        next_btn.set_halign(Gtk.Align.CENTER)
        next_btn.connect("clicked", self._on_type_selected)
        group.add(next_btn)

        page.add(group)
        return page

    def _on_type_selected(self, btn):
        type_idx = self.app.type_combo.get_selected()
        if type_idx == 2:
            self.migration_type = "ata"
            self._push_ata_pages()
        elif type_idx == 1:
            self.migration_type = "desktop"
            self._push_desktop_pages()
        else:
            self.migration_type = "init"
            self._push_init_pages()


    def _push_init_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self._create_init_page(), title="Init Migration"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_init_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="Summary"))

    def _create_init_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Init System Migration")
        detected = self.app.state.get('DETECTED_INIT', 'openrc')

        inits = ["openrc", "runit", "dinit", "s6", "systemd"]
        self.app.init_src_combo = Gtk.DropDown.new(Gtk.StringList.new(inits))
        if detected in inits:
            self.app.init_src_combo.set_selected(inits.index(detected))
        src_row = Adw.ActionRow(title="Source Init", subtitle=f"Current init system (detected: {detected})")
        src_row.add_suffix(self.app.init_src_combo)
        group.add(src_row)

        tgts = ["openrc", "runit", "dinit", "s6"]
        self.app.init_tgt_combo = Gtk.DropDown.new(Gtk.StringList.new(tgts))
        tgt_row = Adw.ActionRow(title="Target Init", subtitle="Select new init system")
        tgt_row.add_suffix(self.app.init_tgt_combo)
        group.add(tgt_row)

        page.add(group)
        return page

    def _update_init_summary(self):
        inits = ["openrc", "runit", "dinit", "s6", "systemd"]
        tgts = ["openrc", "runit", "dinit", "s6"]
        src = inits[self.app.init_src_combo.get_selected()] if hasattr(self.app, 'init_src_combo') else "openrc"
        tgt = tgts[self.app.init_tgt_combo.get_selected()] if hasattr(self.app, 'init_tgt_combo') else "dinit"
        text = f"Migrate init system from {src} to {tgt}\n\n"
        text += "This will:\n"
        text += "- Backup current init configuration\n"
        text += f"- Install {tgt} packages\n"
        text += "- Migrate enabled services\n"
        text += "- Keep custom services in backup"
        self.app.summary_text.get_buffer().set_text(text)


    def _push_desktop_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self._create_desktop_page(), title="Desktop Migration"))
        nav.push(Adw.NavigationPage(child=self._create_de_display_page(), title="Display & Audio"))
        nav.push(Adw.NavigationPage(child=self._create_de_network_page(), title="Network & Extras"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_desktop_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="Summary"))

    def _create_desktop_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Desktop Environment Migration")
        detected = self.app.state.get('DETECTED_DE', 'none')

        des = ["kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
               "i3wm", "dwm", "vxwm", "icewm", "mango", "cinnamon", "budgie", "moksha", "cosmic", "none"]
        self.app.de_src_combo = Gtk.DropDown.new(Gtk.StringList.new(des))
        if detected in des:
            self.app.de_src_combo.set_selected(des.index(detected))
        src_row = Adw.ActionRow(title="Source Desktop", subtitle=f"Current desktop (detected: {detected})")
        src_row.add_suffix(self.app.de_src_combo)
        group.add(src_row)

        self.app.de_tgt_combo = Gtk.DropDown.new(Gtk.StringList.new(des))
        self.app.de_tgt_combo.set_selected(1)
        tgt_row = Adw.ActionRow(title="Target Desktop", subtitle="Select new desktop")
        tgt_row.add_suffix(self.app.de_tgt_combo)
        group.add(tgt_row)

        page.add(group)
        return page

    def _create_de_display_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Display & Audio")

        self.app.de_dm_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "sddm", "lightdm", "soniclogin", "none"]))
        dm_row = Adw.ActionRow(title="Display manager")
        dm_row.add_suffix(self.app.de_dm_combo)
        group.add(dm_row)

        self.app.de_x_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "xlibre", "xorg", "wayland"]))
        x_row = Adw.ActionRow(title="Display stack")
        x_row.add_suffix(self.app.de_x_combo)
        group.add(x_row)

        self.app.de_audio_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "pipewire", "pulseaudio", "none"]))
        audio_row = Adw.ActionRow(title="Audio stack")
        audio_row.add_suffix(self.app.de_audio_combo)
        group.add(audio_row)

        page.add(group)
        return page

    def _create_de_network_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Network & Extras")

        self.app.de_net_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "networkmanager", "dhcpcd+iwd", "connman", "none"]))
        net_row = Adw.ActionRow(title="Network stack")
        net_row.add_suffix(self.app.de_net_combo)
        group.add(net_row)

        extras_label = Gtk.Label(label="Extra packages to ensure are installed:")
        extras_label.set_margin_top(10)
        group.add(extras_label)

        self.app.de_extras_checkboxes = {}
        extras_list = [
            "git", "flatpak", "fastfetch", "firewalld", "bluez", "zram-tools",
            "fzf", "zoxide", "starship", "eza", "btop", "htop", "nvtop", "tmux",
            "nano", "vim", "neovim", "micro", "helix",
            "firefox", "chromium", "qutebrowser",
            "ranger", "lf", "nnn", "thunar",
            "alacritty", "kitty", "foot",
            "mpv", "feh"
        ]
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(200)
        extras_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        for pkg in extras_list:
            check = Gtk.CheckButton(label=pkg)
            extras_box.append(check)
            self.app.de_extras_checkboxes[pkg] = check
        scroll.set_child(extras_box)
        group.add(scroll)

        page.add(group)
        return page

    def _update_desktop_summary(self):
        des = ["kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
               "i3wm", "dwm", "vxwm", "icewm", "mango", "cinnamon", "budgie", "moksha", "cosmic", "none"]
        src = des[self.app.de_src_combo.get_selected()] if hasattr(self.app, 'de_src_combo') else "?"
        tgt = des[self.app.de_tgt_combo.get_selected()] if hasattr(self.app, 'de_tgt_combo') else "?"

        dm_vals = ["current", "sddm", "lightdm", "soniclogin", "none"]
        x_vals = ["current", "xlibre", "xorg", "wayland"]
        audio_vals = ["current", "pipewire", "pulseaudio", "none"]
        net_vals = ["current", "networkmanager", "dhcpcd+iwd", "connman", "none"]

        dm = dm_vals[self.app.de_dm_combo.get_selected()] if hasattr(self.app, 'de_dm_combo') else "current"
        x = x_vals[self.app.de_x_combo.get_selected()] if hasattr(self.app, 'de_x_combo') else "current"
        audio = audio_vals[self.app.de_audio_combo.get_selected()] if hasattr(self.app, 'de_audio_combo') else "current"
        net = net_vals[self.app.de_net_combo.get_selected()] if hasattr(self.app, 'de_net_combo') else "current"
        extras = ""
        if hasattr(self.app, 'de_extras_checkboxes'):
            extras = " ".join([pkg for pkg, cb in self.app.de_extras_checkboxes.items() if cb.get_active()])

        text = f"Migrate desktop from {src} to {tgt}\n\n"
        text += f"Display manager: {dm}\n"
        text += f"Display stack: {x}\n"
        text += f"Audio: {audio}\n"
        text += f"Network: {net}\n"
        text += f"Extras: {extras}\n\n"
        text += "This will:\n"
        text += "- Backup user configurations\n"
        text += f"- Remove {src} packages\n"
        text += f"- Install {tgt} packages"
        self.app.summary_text.get_buffer().set_text(text)


    def _push_ata_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self._create_ata_config_page(), title="ATA Configuration"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_ata_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="ATA Summary"))

    def _create_ata_config_page(self):
        page = Adw.PreferencesPage()

        warn_group = Adw.PreferencesGroup(title="EXPERIMENTAL FEATURE")
        warn_label = Gtk.Label()
        warn_label.set_markup(
            '<span foreground="red" weight="bold">EXPERIMENTAL FEATURE</span>\n\n'
            'This will convert your Arch Linux system to Artix.\n'
            'All user data and configurations will be preserved.\n'
            'Make a full system backup before proceeding.\n\n'
            'Run this from your booted Arch system, not the live ISO.'
        )
        warn_label.set_wrap(True)
        warn_group.add(warn_label)
        page.add(warn_group)

        caps_group = Adw.PreferencesGroup(title="Migration Capabilities")
        capabilities = Gtk.Label()
        capabilities.set_markup(
            '<b>Automatically Migrated:</b>\n'
            '  Packages (with version mismatch warnings)\n'
            '  Desktop environment and display manager\n'
            '  User files and home directories\n'
            '  WiFi passwords and network configs\n'
            '  SSH keys, firewall rules, cron jobs\n'
            '  PAM modules (pam_systemd  pam_elogind)\n'
            '  mkinitcpio hooks (systemd  udev/encrypt)\n'
            '  systemd timers  cron\n'
            '  systemd-boot  GRUB\n'
            '  systemd-homed users  standard /home\n'
            '  Flatpaks and AppImages preserved\n'
            '  DKMS modules auto-rebuild\n'
            '  AUR packages (batch reinstall attempted)\n'
            '\n'
            '<b>Needs Manual Attention:</b>\n'
            '  Snap packages (require systemd)\n'
            '  Complex monotonic timers\n'
            '  Custom systemd unit files (backed up)\n'
        )
        capabilities.set_xalign(0)
        caps_group.add(capabilities)
        page.add(caps_group)

        config_group = Adw.PreferencesGroup(title="ATA Configuration")
        self.app.ata_init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        init_row = Adw.ActionRow(title="Target init system")
        init_row.add_suffix(self.app.ata_init_combo)
        config_group.add(init_row)

        self.app.ata_arch_repos_check = Gtk.Switch()
        self.app.ata_arch_repos_check.set_active(True)
        arch_row = Adw.ActionRow(title="Keep access to Arch repositories", subtitle="Needed for AUR")
        arch_row.add_suffix(self.app.ata_arch_repos_check)
        config_group.add(arch_row)

        self.app.ata_aur_combo = Gtk.DropDown.new(Gtk.StringList.new(["paru", "yay", "Skip"]))
        aur_row = Adw.ActionRow(title="AUR helper for batch reinstall")
        aur_row.add_suffix(self.app.ata_aur_combo)
        config_group.add(aur_row)

        page.add(config_group)
        return page

    def _update_ata_summary(self):
        inits = ["openrc", "runit", "dinit", "s6"]
        init = inits[self.app.ata_init_combo.get_selected()] if hasattr(self.app, 'ata_init_combo') else "dinit"
        arch_repos = "yes" if hasattr(self.app, 'ata_arch_repos_check') and self.app.ata_arch_repos_check.get_active() else "no"
        aur_vals = ["paru", "yay", ""]
        aur_helper = aur_vals[self.app.ata_aur_combo.get_selected()] if hasattr(self.app, 'ata_aur_combo') else ""
        de = self.app.state.get('DETECTED_DE', 'unknown')

        text = "Arch Linux → Artix Migration\n\n"
        text += f"Target init: {init}\n"
        text += f"Arch repositories: {arch_repos}\n"
        text += f"AUR helper: {aur_helper}\n"
        if de and de != 'none':
            text += f"Detected desktop: {de}\n"
        text += "\nThis will:\n"
        text += "  Audit your entire system\n"
        text += "  Back up everything to /arch-migration-backup-*/\n"
        text += "  Convert systemd services, timers, PAM, and hooks\n"
        text += "  Replace all packages with Artix equivalents\n"
        text += "  Reinstall your desktop environment\n"
        text += "  Preserve all user data and configurations\n"
        text += "  Attempt AUR package reinstall\n\n"
        text += "A reboot is required after migration."
        self.app.summary_text.get_buffer().set_text(text)


    def _on_install(self):
        self._collect_state()
        self.app.save_state()

        title = "System Migration"
        if self.migration_type == "ata":
            title = "Arch → Artix Migration"

        self.app.start_installation(title)

    def _collect_state(self):
        if self.migration_type == "ata":
            inits = ["openrc", "runit", "dinit", "s6"]
            self.app.state['MIGRATION_TYPE'] = 'ata'
            self.app.state['MIGRATION_SRC'] = 'arch'
            self.app.state['MIGRATION_TGT'] = inits[self.app.ata_init_combo.get_selected()] if hasattr(self.app, 'ata_init_combo') else "dinit"
            self.app.state['INIT'] = self.app.state['MIGRATION_TGT']
            self.app.state['ENABLE_ARCH_REPOS'] = "yes" if hasattr(self.app, 'ata_arch_repos_check') and self.app.ata_arch_repos_check.get_active() else "no"
            aur_vals = ["paru", "yay", ""]
            self.app.state['ATA_AUR_HELPER'] = aur_vals[self.app.ata_aur_combo.get_selected()] if hasattr(self.app, 'ata_aur_combo') else ""
        elif self.migration_type == "init":
            inits = ["openrc", "runit", "dinit", "s6", "systemd"]
            tgts = ["openrc", "runit", "dinit", "s6"]
            self.app.state['MIGRATION_TYPE'] = 'init'
            self.app.state['MIGRATION_SRC'] = inits[self.app.init_src_combo.get_selected()] if hasattr(self.app, 'init_src_combo') else "openrc"
            self.app.state['MIGRATION_TGT'] = tgts[self.app.init_tgt_combo.get_selected()] if hasattr(self.app, 'init_tgt_combo') else "dinit"
        else:
            des = ["kde", "sonicde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri",
                   "i3wm", "dwm", "vxwm", "icewm", "mango", "cinnamon", "budgie", "moksha", "cosmic", "none"]
            dm_vals = ["current", "sddm", "lightdm", "soniclogin", "none"]
            x_vals = ["current", "xlibre", "xorg", "wayland"]
            audio_vals = ["current", "pipewire", "pulseaudio", "none"]
            net_vals = ["current", "networkmanager", "dhcpcd+iwd", "connman", "none"]

            self.app.state['MIGRATION_TYPE'] = 'desktop'
            self.app.state['MIGRATION_SRC'] = des[self.app.de_src_combo.get_selected()] if hasattr(self.app, 'de_src_combo') else "none"
            self.app.state['MIGRATION_TGT'] = des[self.app.de_tgt_combo.get_selected()] if hasattr(self.app, 'de_tgt_combo') else "xfce"
            self.app.state['DE_MIG_DM'] = dm_vals[self.app.de_dm_combo.get_selected()] if hasattr(self.app, 'de_dm_combo') else "current"
            self.app.state['DE_MIG_X'] = x_vals[self.app.de_x_combo.get_selected()] if hasattr(self.app, 'de_x_combo') else "current"
            self.app.state['DE_MIG_AUDIO'] = audio_vals[self.app.de_audio_combo.get_selected()] if hasattr(self.app, 'de_audio_combo') else "current"
            self.app.state['DE_MIG_NETWORK'] = net_vals[self.app.de_net_combo.get_selected()] if hasattr(self.app, 'de_net_combo') else "current"
            if hasattr(self.app, 'de_extras_checkboxes'):
                extras_selected = [pkg for pkg, cb in self.app.de_extras_checkboxes.items() if cb.get_active()]
                self.app.state['DE_MIG_EXTRAS'] = " ".join(extras_selected)

        self.app.state['MODE'] = 'migrate'
        self.app.state['GUI_MODE'] = 'yes'