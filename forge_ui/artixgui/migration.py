#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
import os
import subprocess
from gi.repository import Gtk
from .base import BaseWindow
from ..backends.gui import ProgressWindow

class MigrationWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="System Migration")
        self.add_page("Migration Type", self.create_type_page())
        self.add_page("Init Migration", self.create_init_page())
        self.add_page("Desktop Migration", self.create_desktop_page())
        self.add_page("DE – Display & Audio", self.create_de_display_page())
        self.add_page("DE – Network & Extras", self.create_de_network_page())
        self.add_page("Summary", self.create_summary_page())

        self.migration_type = None
        self.init_source = None
        self.init_target = None
        self.desktop_source = None
        self.desktop_target = None

        # Auto-detect current init and desktop
        self.detect_current_system()

    def detect_current_system(self):
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
            result = subprocess.run(
                ["sudo", "bash", "-c", script],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, val = line.split('=', 1)
                    if key == "INIT":
                        self.state['DETECTED_INIT'] = val
                    elif key == "WM_DE":
                        self.state['DETECTED_DE'] = val
        except Exception:
            pass

    def create_type_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">System Migration</span>')
        box.pack_start(label, False, False, 0)

        detected = ""
        if self.state.get('DETECTED_INIT'):
            detected += f"\nDetected init: {self.state['DETECTED_INIT']}"
        if self.state.get('DETECTED_DE'):
            detected += f"\nDetected desktop: {self.state['DETECTED_DE']}"
        if detected:
            det_label = Gtk.Label(label=detected)
            box.pack_start(det_label, False, False, 5)

        desc = Gtk.Label()
        desc.set_text("Choose what you want to migrate:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)

        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append_text("Init System (openrc ↔ runit ↔ dinit ↔ s6 ↔ systemd)")
        self.type_combo.append_text("Desktop Environment (KDE ↔ XFCE ↔ Sway etc.)")
        self.type_combo.set_active(0)
        box.pack_start(self.type_combo, False, False, 5)
        return box

    def create_init_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Init System Migration</span>')
        box.pack_start(label, False, False, 0)

        detected = self.state.get('DETECTED_INIT', 'openrc')
        src_label = Gtk.Label(label=f"Current init system (detected: {detected}):", xalign=0)
        box.pack_start(src_label, False, False, 5)
        self.init_src_combo = Gtk.ComboBoxText()
        inits = ["openrc", "runit", "dinit", "s6", "systemd"]
        for init in inits:
            self.init_src_combo.append_text(init)
        # Set active to detected if possible
        if detected in inits:
            self.init_src_combo.set_active(inits.index(detected))
        else:
            self.init_src_combo.set_active(0)
        box.pack_start(self.init_src_combo, False, False, 0)

        tgt_label = Gtk.Label(label="Target init system:", xalign=0)
        box.pack_start(tgt_label, False, False, 5)
        self.init_tgt_combo = Gtk.ComboBoxText()
        for init in ["openrc", "runit", "dinit", "s6"]:
            self.init_tgt_combo.append_text(init)
        self.init_tgt_combo.set_active(0)
        box.pack_start(self.init_tgt_combo, False, False, 0)
        return box

    def create_desktop_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Desktop Environment Migration</span>')
        box.pack_start(label, False, False, 0)

        detected = self.state.get('DETECTED_DE', 'none')
        src_label = Gtk.Label(label=f"Current desktop (detected: {detected}):", xalign=0)
        box.pack_start(src_label, False, False, 5)
        self.de_src_combo = Gtk.ComboBoxText()
        des = ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]
        for de in des:
            self.de_src_combo.append_text(de)
        if detected in des:
            self.de_src_combo.set_active(des.index(detected))
        else:
            self.de_src_combo.set_active(0)
        box.pack_start(self.de_src_combo, False, False, 0)

        tgt_label = Gtk.Label(label="Target desktop:", xalign=0)
        box.pack_start(tgt_label, False, False, 5)
        self.de_tgt_combo = Gtk.ComboBoxText()
        for de in des:
            self.de_tgt_combo.append_text(de)
        self.de_tgt_combo.set_active(1)
        box.pack_start(self.de_tgt_combo, False, False, 0)
        return box

    def create_de_display_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Display & Audio</span>')
        box.pack_start(label, False, False, 0)

        dm_label = Gtk.Label(label="Display manager:", xalign=0)
        box.pack_start(dm_label, False, False, 5)
        self.de_dm_combo = Gtk.ComboBoxText()
        for dm in ["current", "sddm", "lightdm", "soniclogin", "none"]:
            self.de_dm_combo.append_text(dm)
        self.de_dm_combo.set_active(0)
        box.pack_start(self.de_dm_combo, False, False, 0)

        x_label = Gtk.Label(label="Display stack:", xalign=0)
        box.pack_start(x_label, False, False, 5)
        self.de_x_combo = Gtk.ComboBoxText()
        for x in ["current", "xlibre", "xorg", "wayland"]:
            self.de_x_combo.append_text(x)
        self.de_x_combo.set_active(0)
        box.pack_start(self.de_x_combo, False, False, 0)

        audio_label = Gtk.Label(label="Audio stack:", xalign=0)
        box.pack_start(audio_label, False, False, 5)
        self.de_audio_combo = Gtk.ComboBoxText()
        for a in ["current", "pipewire", "pulseaudio", "none"]:
            self.de_audio_combo.append_text(a)
        self.de_audio_combo.set_active(0)
        box.pack_start(self.de_audio_combo, False, False, 0)
        return box

    def create_de_network_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Network & Extras</span>')
        box.pack_start(label, False, False, 0)

        net_label = Gtk.Label(label="Network stack:", xalign=0)
        box.pack_start(net_label, False, False, 5)
        self.de_net_combo = Gtk.ComboBoxText()
        for n in ["current", "networkmanager", "dhcpcd+iwd", "connman", "none"]:
            self.de_net_combo.append_text(n)
        self.de_net_combo.set_active(0)
        box.pack_start(self.de_net_combo, False, False, 0)

        extras_label = Gtk.Label(label="Extra packages to ensure are installed:", xalign=0)
        box.pack_start(extras_label, False, False, 10)
        self.de_extras_checkboxes = {}
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
            extras_box.pack_start(check, False, False, 0)
            self.de_extras_checkboxes[pkg] = check
        scroll.add(extras_box)
        box.pack_start(scroll, True, True, 0)
        return box

    def create_summary_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Ready to Migrate</span>')
        box.pack_start(label, False, False, 0)
        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        self.summary_text.set_size_request(400, 200)
        box.pack_start(self.summary_text, False, False, 10)
        warn_label = Gtk.Label()
        warn_label.set_markup('<span foreground="red">Migration may cause system instability.\nBackup your data before proceeding.</span>')
        box.pack_start(warn_label, False, False, 5)
        return box

    def update_summary(self):
        self.collect_state()
        if self.migration_type == "init":
            text = f"Migrate init system from {self.init_source} to {self.init_target}\n\nThis will:\n- Backup current init configuration\n- Install {self.init_target} packages\n- Migrate enabled services\n- Keep custom services in backup"
        else:
            src = self.desktop_source or "?"
            tgt = self.desktop_target or "?"
            dm = self.state.get('DE_MIG_DM', 'current')
            x = self.state.get('DE_MIG_X', 'current')
            audio = self.state.get('DE_MIG_AUDIO', 'current')
            net = self.state.get('DE_MIG_NETWORK', 'current')
            extras = self.state.get('DE_MIG_EXTRAS', '')
            text = f"Migrate desktop from {src} to {tgt}\n\nDisplay manager: {dm}\nDisplay stack: {x}\nAudio: {audio}\nNetwork: {net}\nExtras: {extras}\n\nThis will:\n- Backup user configurations\n- Remove {src} packages\n- Install {tgt} packages"
        self.summary_text.get_buffer().set_text(text)

    def collect_state(self):
        self.migration_type = "init" if self.type_combo.get_active_text().startswith("Init") else "desktop"
        if self.migration_type == "init":
            self.init_source = self.init_src_combo.get_active_text()
            self.init_target = self.init_tgt_combo.get_active_text()
            self.state['MIGRATION_TYPE'] = 'init'
            self.state['MIGRATION_SRC'] = self.init_source
            self.state['MIGRATION_TGT'] = self.init_target
        else:
            self.desktop_source = self.de_src_combo.get_active_text()
            self.desktop_target = self.de_tgt_combo.get_active_text()
            self.state['MIGRATION_TYPE'] = 'desktop'
            self.state['MIGRATION_SRC'] = self.desktop_source
            self.state['MIGRATION_TGT'] = self.desktop_target
            # DE-specific choices
            self.state['DE_MIG_DM'] = self.de_dm_combo.get_active_text() if hasattr(self, 'de_dm_combo') else "current"
            self.state['DE_MIG_X'] = self.de_x_combo.get_active_text() if hasattr(self, 'de_x_combo') else "current"
            self.state['DE_MIG_AUDIO'] = self.de_audio_combo.get_active_text() if hasattr(self, 'de_audio_combo') else "current"
            self.state['DE_MIG_NETWORK'] = self.de_net_combo.get_active_text() if hasattr(self, 'de_net_combo') else "current"
            extras_selected = []
            if hasattr(self, 'de_extras_checkboxes'):
                for pkg, cb in self.de_extras_checkboxes.items():
                    if cb.get_active():
                        extras_selected.append(pkg)
            self.state['DE_MIG_EXTRAS'] = " ".join(extras_selected)

        self.state['MODE'] = 'migrate'
        self.state['GUI_MODE'] = 'yes'

    def start_installation(self):
        self.collect_state()
        self.save_state()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        install_script = os.path.join(base_dir, "..", "install")

        self.window.hide()
        progress = ProgressWindow(
            {"title": "System Migration", "command": ["sudo", install_script, "--non-interactive"]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()

        if result.get("result") == "success":
            dialog = Gtk.MessageDialog(parent=None, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                       message_format="Migration completed successfully!\n\nReboot recommended.")
        else:
            dialog = Gtk.MessageDialog(parent=None, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                       message_format="Migration failed. Check logs.")
        dialog.run()
        dialog.destroy()
        Gtk.main_quit()

    def on_next(self, widget):
        if self.current_page == 0:
            self.migration_type = "init" if self.type_combo.get_active_text().startswith("Init") else "desktop"
            if self.migration_type == "init":
                self.stack.set_visible_child(self.pages[1])
                self.current_page = 1
            else:
                self.stack.set_visible_child(self.pages[2])
                self.current_page = 2
            self.update_nav_buttons()
        elif self.current_page == 1:
            # Init migration: go directly to summary
            self.stack.set_visible_child(self.pages[5])
            self.current_page = 5
            self.update_summary()
            self.update_nav_buttons()
        elif self.current_page == 2:
            # Desktop migration: go to display page
            self.stack.set_visible_child(self.pages[3])
            self.current_page = 3
            self.update_nav_buttons()
        elif self.current_page == 3:
            # Go to network/extras page
            self.stack.set_visible_child(self.pages[4])
            self.current_page = 4
            self.update_nav_buttons()
        elif self.current_page == 4:
            # Go to summary
            self.stack.set_visible_child(self.pages[5])
            self.current_page = 5
            self.update_summary()
            self.update_nav_buttons()
        else:
            self.start_installation()