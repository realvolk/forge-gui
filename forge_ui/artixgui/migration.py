#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
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
        self.detect_current_system()
        self.migration_stage_file = "/tmp/artix-installer/migration-stage.conf"
        if os.path.exists(self.migration_stage_file):
            self.add_page("Resume Migration", self.create_resume_page())
    
    def create_resume_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Resume Migration</span>')
        box.append(label)
        desc = Gtk.Label()
        with open(self.migration_stage_file) as f:
            stage = f.read().strip()
        desc.set_text(f"A previous migration was interrupted at stage: {stage}\n\nClick Resume to continue, or Start Fresh to begin a new migration.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        resume_btn = Gtk.Button(label="Resume")
        resume_btn.connect("clicked", lambda b: self.start_installation())
        box.append(resume_btn)
        fresh_btn = Gtk.Button(label="Start Fresh")
        fresh_btn.connect("clicked", self.on_fresh_migration)
        box.append(fresh_btn)
        return box
    
    def on_fresh_migration(self, widget):
        if os.path.exists(self.migration_stage_file):
            os.remove(self.migration_stage_file)
        self.stack.set_visible_child(self.pages[0])
        self.current_page = 0
        self.update_nav_buttons()

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
            result = subprocess.run(["sudo", "bash", "-c", script], capture_output=True, text=True, timeout=30)
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
        box.append(label)
        detected = ""
        if self.state.get('DETECTED_INIT'):
            detected += f"\nDetected init: {self.state['DETECTED_INIT']}"
        if self.state.get('DETECTED_DE'):
            detected += f"\nDetected desktop: {self.state['DETECTED_DE']}"
        if detected:
            det_label = Gtk.Label(label=detected)
            box.append(det_label)
        desc = Gtk.Label()
        desc.set_text("Choose what you want to migrate:")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.type_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "Init System (openrc ↔ runit ↔ dinit ↔ s6 ↔ systemd)",
            "Desktop Environment (KDE ↔ XFCE ↔ Sway etc.)"
        ]))
        box.append(self.type_combo)
        return box

    def create_init_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Init System Migration</span>')
        box.append(label)
        detected = self.state.get('DETECTED_INIT', 'openrc')
        src_label = Gtk.Label(label=f"Current init system (detected: {detected}):", xalign=0)
        box.append(src_label)
        inits = ["openrc", "runit", "dinit", "s6", "systemd"]
        self.init_src_combo = Gtk.DropDown.new(Gtk.StringList.new(inits))
        if detected in inits:
            self.init_src_combo.set_selected(inits.index(detected))
        box.append(self.init_src_combo)
        tgt_label = Gtk.Label(label="Target init system:", xalign=0)
        box.append(tgt_label)
        self.init_tgt_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        box.append(self.init_tgt_combo)
        return box

    def create_desktop_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Desktop Environment Migration</span>')
        box.append(label)
        detected = self.state.get('DETECTED_DE', 'none')
        src_label = Gtk.Label(label=f"Current desktop (detected: {detected}):", xalign=0)
        box.append(src_label)
        des = ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]
        self.de_src_combo = Gtk.DropDown.new(Gtk.StringList.new(des))
        if detected in des:
            self.de_src_combo.set_selected(des.index(detected))
        box.append(self.de_src_combo)
        tgt_label = Gtk.Label(label="Target desktop:", xalign=0)
        box.append(tgt_label)
        self.de_tgt_combo = Gtk.DropDown.new(Gtk.StringList.new(des))
        self.de_tgt_combo.set_selected(1)
        box.append(self.de_tgt_combo)
        return box

    def create_de_display_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Display & Audio</span>')
        box.append(label)
        dm_label = Gtk.Label(label="Display manager:", xalign=0)
        box.append(dm_label)
        self.de_dm_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "sddm", "lightdm", "soniclogin", "none"]))
        box.append(self.de_dm_combo)
        x_label = Gtk.Label(label="Display stack:", xalign=0)
        box.append(x_label)
        self.de_x_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "xlibre", "xorg", "wayland"]))
        box.append(self.de_x_combo)
        audio_label = Gtk.Label(label="Audio stack:", xalign=0)
        box.append(audio_label)
        self.de_audio_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "pipewire", "pulseaudio", "none"]))
        box.append(self.de_audio_combo)
        return box

    def create_de_network_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Network & Extras</span>')
        box.append(label)
        net_label = Gtk.Label(label="Network stack:", xalign=0)
        box.append(net_label)
        self.de_net_combo = Gtk.DropDown.new(Gtk.StringList.new(["current", "networkmanager", "dhcpcd+iwd", "connman", "none"]))
        box.append(self.de_net_combo)
        extras_label = Gtk.Label(label="Extra packages to ensure are installed:", xalign=0)
        box.append(extras_label)
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
            extras_box.append(check)
            self.de_extras_checkboxes[pkg] = check
        scroll.set_child(extras_box)
        box.append(scroll)
        return box

    def create_summary_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Ready to Migrate</span>')
        box.append(label)
        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        self.summary_text.set_size_request(400, 200)
        box.append(self.summary_text)
        warn_label = Gtk.Label()
        warn_label.set_markup('<span foreground="red">Migration may cause system instability.\nBackup your data before proceeding.</span>')
        box.append(warn_label)
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

    def _get_combo_text(self, combo, values):
        idx = combo.get_selected()
        return values[idx] if 0 <= idx < len(values) else values[0]

    def collect_state(self):
        type_idx = self.type_combo.get_selected()
        self.migration_type = "init" if type_idx == 0 else "desktop"
        if self.migration_type == "init":
            inits = ["openrc", "runit", "dinit", "s6", "systemd"]
            tgts = ["openrc", "runit", "dinit", "s6"]
            self.init_source = self._get_combo_text(self.init_src_combo, inits)
            self.init_target = self._get_combo_text(self.init_tgt_combo, tgts)
            self.state['MIGRATION_TYPE'] = 'init'
            self.state['MIGRATION_SRC'] = self.init_source
            self.state['MIGRATION_TGT'] = self.init_target
        else:
            des = ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]
            self.desktop_source = self._get_combo_text(self.de_src_combo, des)
            self.desktop_target = self._get_combo_text(self.de_tgt_combo, des)
            self.state['MIGRATION_TYPE'] = 'desktop'
            self.state['MIGRATION_SRC'] = self.desktop_source
            self.state['MIGRATION_TGT'] = self.desktop_target
            self.state['DE_MIG_DM'] = self._get_combo_text(self.de_dm_combo, ["current", "sddm", "lightdm", "soniclogin", "none"])
            self.state['DE_MIG_X'] = self._get_combo_text(self.de_x_combo, ["current", "xlibre", "xorg", "wayland"])
            self.state['DE_MIG_AUDIO'] = self._get_combo_text(self.de_audio_combo, ["current", "pipewire", "pulseaudio", "none"])
            self.state['DE_MIG_NETWORK'] = self._get_combo_text(self.de_net_combo, ["current", "networkmanager", "dhcpcd+iwd", "connman", "none"])
            extras_selected = [pkg for pkg, cb in self.de_extras_checkboxes.items() if cb.get_active()]
            self.state['DE_MIG_EXTRAS'] = " ".join(extras_selected)
        self.state['MODE'] = 'migrate'
        self.state['GUI_MODE'] = 'yes'

    def start_installation(self):
        self.collect_state()
        self.save_state()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        install_script = os.path.join(base_dir, "install")
        self.window.hide()
        progress = ProgressWindow(
            {"title": "System Migration", "command": [install_script, "--non-interactive"]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()
        msg = "Migration completed successfully!\n\nReboot recommended." if result.get("result") == "success" else "Migration failed. Check logs."
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
                                   message_type=Gtk.MessageType.INFO if result.get("result") == "success" else Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK, text=msg)
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())

    def on_next(self, widget):
        if self.current_page == 0:
            self.migration_type = "init" if self.type_combo.get_selected() == 0 else "desktop"
            if self.migration_type == "init":
                self.stack.set_visible_child(self.pages[1])
                self.current_page = 1
            else:
                self.stack.set_visible_child(self.pages[2])
                self.current_page = 2
            self.update_nav_buttons()
        elif self.current_page == 1:
            self.stack.set_visible_child(self.pages[5])
            self.current_page = 5
            self.update_summary()
            self.update_nav_buttons()
        elif self.current_page == 2:
            self.stack.set_visible_child(self.pages[3])
            self.current_page = 3
            self.update_nav_buttons()
        elif self.current_page == 3:
            self.stack.set_visible_child(self.pages[4])
            self.current_page = 4
            self.update_nav_buttons()
        elif self.current_page == 4:
            self.stack.set_visible_child(self.pages[5])
            self.current_page = 5
            self.update_summary()
            self.update_nav_buttons()
        else:
            self.start_installation()