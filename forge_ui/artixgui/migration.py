#!/usr/bin/env python3
import subprocess
import os
from gi.repository import Gtk
from .base import BaseWindow

class MigrationWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="System Migration")
        self.add_page("Migration Type", self.create_type_page())
        self.add_page("Init Migration", self.create_init_page())
        self.add_page("Desktop Migration", self.create_desktop_page())
        self.add_page("Summary", self.create_summary_page())
        self.migration_type = None
        self.init_source = None
        self.init_target = None
        self.desktop_source = None
        self.desktop_target = None

    def create_type_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">System Migration</span>')
        box.pack_start(label, False, False, 0)

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

        src_label = Gtk.Label(label="Current init system:", xalign=0)
        box.pack_start(src_label, False, False, 5)
        self.init_src_combo = Gtk.ComboBoxText()
        for init in ["openrc", "runit", "dinit", "s6", "systemd"]:
            self.init_src_combo.append_text(init)
        # Detect current init
        current = self.detect_current_init()
        if current:
            self.init_src_combo.set_active([self.init_src_combo.get_model()[i][0] for i in range(self.init_src_combo.get_model().get_iter_first().get_value(0))].index(current) if current in [self.init_src_combo.get_model()[i][0] for i in range(self.init_src_combo.get_model().get_iter_first().get_value(0))] else 0)
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

    def detect_current_init(self):
        if os.path.isdir("/etc/runit"):
            return "runit"
        elif os.path.isdir("/etc/dinit.d"):
            return "dinit"
        elif os.path.isdir("/etc/s6"):
            return "s6"
        elif os.path.isdir("/etc/systemd"):
            return "systemd"
        else:
            return "openrc"

    def create_desktop_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Desktop Environment Migration</span>')
        box.pack_start(label, False, False, 0)

        src_label = Gtk.Label(label="Current desktop:", xalign=0)
        box.pack_start(src_label, False, False, 5)
        self.de_src_combo = Gtk.ComboBoxText()
        des = ["kde", "xfce", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]
        for de in des:
            self.de_src_combo.append_text(de)
        current_de = self.detect_current_de()
        if current_de:
            self.de_src_combo.set_active(des.index(current_de) if current_de in des else 0)
        else:
            self.de_src_combo.set_active(0)
        box.pack_start(self.de_src_combo, False, False, 0)

        tgt_label = Gtk.Label(label="Target desktop:", xalign=0)
        box.pack_start(tgt_label, False, False, 5)
        self.de_tgt_combo = Gtk.ComboBoxText()
        for de in des:
            self.de_tgt_combo.append_text(de)
        self.de_tgt_combo.set_active(1)  # xfce as example
        box.pack_start(self.de_tgt_combo, False, False, 0)

        return box

    def detect_current_de(self):
        packages = {
            "plasma-desktop": "kde",
            "xfce4": "xfce",
            "lxqt": "lxqt",
            "lxde-common": "lxde",
            "hyprland": "hyprland",
            "sway": "sway",
            "niri": "niri",
            "i3-wm": "i3wm",
            "dwm": "dwm",
            "vxwm": "vxwm",
            "icewm": "icewm",
            "mangowm": "mango"
        }
        for pkg, de in packages.items():
            if subprocess.call(['pacman', '-Q', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                return de
        return "none"

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
        if self.migration_type == "init":
            src = self.init_src_combo.get_active_text()
            tgt = self.init_tgt_combo.get_active_text()
            text = f"Migrate init system from {src} to {tgt}\n\nThis will:\n- Backup current init configuration\n- Install {tgt} packages\n- Migrate enabled services\n- Keep custom services in backup"
        else:
            src = self.de_src_combo.get_active_text()
            tgt = self.de_tgt_combo.get_active_text()
            text = f"Migrate desktop from {src} to {tgt}\n\nThis will:\n- Backup user configurations (~/.config, ~/.local, ~/.cache)\n- Remove {src} packages\n- Install {tgt} packages\n- Optionally adjust display manager, display stack, audio, network"
        self.summary_text.get_buffer().set_text(text)

    def collect_state(self):
        self.migration_type = "init" if self.type_combo.get_active_text().startswith("Init") else "desktop"
        if self.migration_type == "init":
            self.init_source = self.init_src_combo.get_active_text()
            self.init_target = self.init_tgt_combo.get_active_text()
        else:
            self.desktop_source = self.de_src_combo.get_active_text()
            self.desktop_target = self.de_tgt_combo.get_active_text()

    def start_installation(self):
        self.collect_state()
        # Get the base directory (where install script lives)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        base_dir = os.path.join(base_dir, "..")
        
        if self.migration_type == "init":
            # Call the appropriate init migration script
            script = f"{base_dir}/migrations/inits/{self.init_source}-to-{self.init_target}.sh"
            if not os.path.exists(script):
                # Fallback to hub-based migration (source -> openrc -> target)
                if self.init_source != "openrc":
                    script1 = f"{base_dir}/migrations/inits/{self.init_source}-to-openrc.sh"
                    script2 = f"{base_dir}/migrations/inits/openrc-to-{self.init_target}.sh"
                    cmd = f"bash {script1} && bash {script2}"
                else:
                    cmd = f"bash {script}"
            else:
                cmd = f"bash {script}"
        else:
            # Call desktop migration script
            script = f"{base_dir}/migrations/des/{self.desktop_source}-to-{self.desktop_target}.sh"
            if not os.path.exists(script):
                # Fallback to any-to.sh with source and target as arguments
                cmd = f"source {base_dir}/migrations/des/common.sh && run_de_migration {self.desktop_source} {self.desktop_target}"
            else:
                cmd = f"bash {script}"

        # Run migration with progress window
        from ..backends.gui import ProgressWindow
        progress = ProgressWindow(
            {"title": "System Migration", "command": ["bash", "-c", cmd]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()

        if result.get("result") == "success":
            dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                       message_format="Migration completed successfully!\n\nReboot recommended.")
            dialog.run()
            dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                       type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                       message_format="Migration failed. Check logs.")
            dialog.run()
            dialog.destroy()
        Gtk.main_quit()

    def on_next(self, widget):
        if self.current_page == 0:  # Type page
            self.migration_type = "init" if self.type_combo.get_active_text().startswith("Init") else "desktop"
            if self.migration_type == "init":
                self.stack.set_visible_child(self.pages[1])
                self.current_page = 1
            else:
                self.stack.set_visible_child(self.pages[2])
                self.current_page = 2
            self.update_nav_buttons()
        elif self.current_page == 1 or self.current_page == 2:
            self.update_summary()
            self.stack.set_visible_child(self.pages[3])
            self.current_page = 3
            self.update_nav_buttons()
        else:
            self.start_installation()