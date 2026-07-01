#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import os
import subprocess
import hashlib
from gi.repository import Gtk, Adw, Gdk, GLib, Pango
from ..backends.gui import ProgressPage
from ..theme import get_colors, ACCENT_COLORS


class InstallerApp(Adw.Application):
    def __init__(self, state_file):
        super().__init__(application_id="com.artixforge.installer")
        self.state_file = state_file
        self.state = {}
        self.load_state()
        self.nav_view = Adw.NavigationView()

        self.window = Adw.ApplicationWindow(application=self)
        self.window.set_default_size(720, 520)
        self.window.set_title("ArtixForge Installer")
        self.window.set_content(self.nav_view)

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        self.window.set_titlebar(header)

        self._apply_theme()
        self._build_package_index()

        from .mode_select import ModeSelectPage
        self.nav_view.push(Adw.NavigationPage(
            child=ModeSelectPage(self), title="Select Installation Mode"
        ))

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            value = value.strip('"').replace('\\"', '"')
                            self.state[key] = value
            except Exception:
                pass

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                for key, value in self.state.items():
                    f.write(f'{key}="{value}"\n')
        except Exception as e:
            print(f"Error saving state: {e}")

    def _build_package_index(self):
        self._package_index = []
        try:
            result = subprocess.run(
                ['pacman', '-Sl', 'world', 'galaxy'],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        self._package_index.append(parts[1])
        except Exception:
            self._package_index = []

    def _apply_theme(self):
        light = self.state.get("GUI_BACKGROUND", "black") == "white"
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(
            Adw.ColorScheme.FORCE_LIGHT if light else Adw.ColorScheme.FORCE_DARK
        )
        title_color_str = self.state.get("GUM_TITLE_COLOR", "212")
        try:
            tc = int(title_color_str)
            accent_tuple = ACCENT_COLORS.get(tc)
            if accent_tuple:
                accent_color = Adw.AccentColor(*accent_tuple)
                style_manager.set_accent_color(accent_color)
        except (ValueError, TypeError):
            pass


    def create_welcome_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER); box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="x-large" weight="bold">Welcome to ArtixForge</span>')
        box.append(label)

        info_text = "System Information:\n"
        try:
            cpu = subprocess.check_output("lscpu | grep 'Model name' | cut -d: -f2 | xargs", shell=True, text=True).strip()
            ram = subprocess.check_output("free -h | awk '/^Mem:/ {print $2}'", shell=True, text=True).strip()
            disk = subprocess.check_output("lsblk -dno NAME,SIZE | head -5", shell=True, text=True).strip()
            info_text += f"CPU: {cpu}\nRAM: {ram}\nDisks:\n{disk}"
        except Exception:
            info_text += "(could not detect)"
        sysinfo = Gtk.Label(label=info_text)
        sysinfo.set_justify(Gtk.Justification.LEFT); sysinfo.set_margin_top(10)
        box.append(sysinfo)

        desc = Gtk.Label()
        desc.set_text("This installer will guide you through installing Artix Linux.\n\nPress Next to begin.")
        desc.set_justify(Gtk.Justification.CENTER); desc.set_margin_top(10)
        box.append(desc)

        group.add(box)
        page.add(group)
        return page

    def create_theme_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Appearance")
        self.theme_combo = Gtk.DropDown.new(Gtk.StringList.new(["ArtixForge", "Artix", "Jet Black", "Mono", "Retro"]))
        self.theme_combo.set_selected(0)
        row = Adw.ActionRow(title="Theme", subtitle="Select color scheme")
        row.add_suffix(self.theme_combo)
        group.add(row)

        self.bg_switch = Gtk.Switch()
        bg_row = Adw.ActionRow(title="White background", subtitle="Use light mode")
        bg_row.add_suffix(self.bg_switch)
        group.add(bg_row)

        def on_theme_changed(dropdown, _param):
            themes = ["ArtixForge", "Artix", "Jet Black", "Mono", "Retro"]
            idx = dropdown.get_selected()
            if 0 <= idx < len(themes):
                colors = {
                    "ArtixForge": ("212", "34"),
                    "Artix": ("39", "117"),
                    "Jet Black": ("245", "196"),
                    "Mono": ("250", "255"),
                    "Retro": ("3", "11"),
                }
                tc, ac = colors.get(themes[idx], ("212", "34"))
                self.state['GUM_TITLE_COLOR'] = tc
                self.state['GUM_ACCENT_COLOR'] = ac
                self._apply_theme()

        self.theme_combo.connect("notify::selected", on_theme_changed)
        self.bg_switch.connect("state-set", lambda sw, state: self.state.update({"GUI_BACKGROUND": "white" if state else "black"}) or self._apply_theme())

        page.add(group)
        return page

    def create_filesystem_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Filesystem")
        self.fs_combo = Gtk.DropDown.new(Gtk.StringList.new(["ext4", "btrfs", "xfs", "f2fs"]))
        row = Adw.ActionRow(title="Type", subtitle="Root filesystem")
        row.add_suffix(self.fs_combo)
        group.add(row)

        self.btrfs_layout_combo = Gtk.DropDown.new(Gtk.StringList.new(["standard", "flat", "snapshot"]))
        btrfs_row = Adw.ActionRow(title="BTRFS Layout", subtitle="Subvolume layout")
        btrfs_row.add_suffix(self.btrfs_layout_combo)
        btrfs_row.set_visible(False)
        group.add(btrfs_row)

        def on_fs_changed(dropdown, _param):
            btrfs_row.set_visible(dropdown.get_selected() == 1)

        self.fs_combo.connect("notify::selected", on_fs_changed)
        page.add(group)
        return page

    def create_bootloader_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Bootloader")
        artix_boot_mode = os.environ.get("ARTIX_BOOT_MODE", "uefi")
        bl_list = ["grub"] if artix_boot_mode == "bios" else ["grub", "refind", "efistub", "limine"]
        self.bl_combo = Gtk.DropDown.new(Gtk.StringList.new(bl_list))
        row = Adw.ActionRow(title="Bootloader", subtitle="System boot method")
        row.add_suffix(self.bl_combo)
        group.add(row)

        self.uki_switch = Gtk.Switch()
        uki_row = Adw.ActionRow(title="Generate UKI", subtitle="Unified Kernel Image")
        uki_row.add_suffix(self.uki_switch)
        if artix_boot_mode == "bios":
            uki_row.set_visible(False)
        group.add(uki_row)

        page.add(group)
        return page

    def create_kernel_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Kernel & Microcode")
        self.kernel_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "linux", "linux-zen", "linux-lts", "linux-hardened",
            "linux-libre", "linux-cachyos-bore", "linux-bazzite-bin",
            "xanmod", "tkg"
        ]))
        row = Adw.ActionRow(title="Kernel", subtitle="Linux kernel version")
        row.add_suffix(self.kernel_combo)
        group.add(row)

        self.microcode_combo = Gtk.DropDown.new(Gtk.StringList.new(["auto", "intel-ucode", "amd-ucode", "none"]))
        mc_row = Adw.ActionRow(title="Microcode", subtitle="CPU microcode updates")
        mc_row.add_suffix(self.microcode_combo)
        group.add(mc_row)

        page.add(group)
        return page

    def create_init_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Init System")
        self.init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        row = Adw.ActionRow(title="Init", subtitle="Service manager")
        row.add_suffix(self.init_combo)
        group.add(row)
        page.add(group)
        return page

    def create_desktop_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Desktop Environment")
        self.de_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "kde", "sonicde", "xfce4", "lxqt", "lxde", "hyprland", "sway",
            "niri", "i3wm", "dwm", "vxwm", "icewm", "mango",
            "cinnamon", "budgie", "moksha", "cosmic", "none"
        ]))
        row = Adw.ActionRow(title="Desktop / WM", subtitle="Graphical environment")
        row.add_suffix(self.de_combo)
        group.add(row)

        self.xstack_combo = Gtk.DropDown.new(Gtk.StringList.new(["xlibre", "xorg"]))
        xs_row = Adw.ActionRow(title="Display Stack", subtitle="X11 implementation")
        xs_row.add_suffix(self.xstack_combo)
        group.add(xs_row)

        self.dm_combo = Gtk.DropDown.new(Gtk.StringList.new(["none", "lightdm", "sddm", "soniclogin"]))
        dm_row = Adw.ActionRow(title="Display Manager", subtitle="Login screen")
        dm_row.add_suffix(self.dm_combo)
        group.add(dm_row)

        page.add(group)
        return page

    def create_network_audio_page(self):
        page = Adw.PreferencesPage()
        net_group = Adw.PreferencesGroup(title="Network")
        self.net_combo = Gtk.DropDown.new(Gtk.StringList.new(["networkmanager", "dhcpcd+iwd", "connman", "none"]))
        row = Adw.ActionRow(title="Network Stack", subtitle="Connection management")
        row.add_suffix(self.net_combo)
        net_group.add(row)

        audio_group = Adw.PreferencesGroup(title="Audio")
        self.audio_combo = Gtk.DropDown.new(Gtk.StringList.new(["pipewire", "pulseaudio", "none"]))
        aud_row = Adw.ActionRow(title="Audio Stack", subtitle="Sound server")
        aud_row.add_suffix(self.audio_combo)
        audio_group.add(aud_row)

        page.add(net_group); page.add(audio_group)
        return page

    def create_extras_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="User Shell & Extras")

        shell_combo = Gtk.DropDown.new(Gtk.StringList.new(["bash", "zsh", "fish"]))
        shell_row = Adw.ActionRow(title="User Shell", subtitle="Default shell")
        shell_row.add_suffix(shell_combo)
        group.add(shell_row)

        notebook = Gtk.Notebook()
        self.__extras_checkboxes = {}

        categories = {
            "System Tools": ["git", "flatpak", "fastfetch", "firewalld", "bluez", "zram-tools", "usb_modeswitch"],
            "Editors": ["nano", "vim", "neovim", "micro", "helix"],
            "Browsers": ["firefox", "chromium", "qutebrowser"],
            "File Managers": ["ranger", "lf", "nnn", "thunar"],
            "Terminals": ["alacritty", "kitty", "foot"],
            "Shell & Prompt": ["fzf", "zoxide", "starship", "eza", "tmux"],
            "Monitoring": ["btop", "htop", "nvtop"],
            "Media": ["mpv", "feh"],
        }

        for cat_name, pkgs in categories.items():
            cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            for pkg in pkgs:
                check = Gtk.CheckButton(label=pkg)
                cat_box.append(check)
                self.__extras_checkboxes[pkg] = check
            notebook.append_page(cat_box, Gtk.Label(label=cat_name))

        group.add(notebook)
        page.add(group)
        return page

    def create_users_page(self):
        page = Adw.PreferencesPage()

        sys_group = Adw.PreferencesGroup(title="System Settings")
        entries = [
            ("Hostname", "artix", "HOSTNAME"),
            ("Timezone", "Europe/Belgrade", "TIMEZONE"),
            ("Locale", "en_US.UTF-8", "LOCALE"),
            ("Keyboard layout", "us", "KEYMAP"),
        ]
        for label, default, key in entries:
            entry = Gtk.Entry()
            entry.set_text(default)
            entry.connect("changed", lambda e, k=key: self.state.update({k: e.get_text()}))
            row = Adw.ActionRow(title=label)
            row.add_suffix(entry)
            sys_group.add(row)
        page.add(sys_group)

        self.users_group = Adw.PreferencesGroup(title="User Accounts")
        self._rebuild_user_list()
        page.add(self.users_group)

        btn_box = Gtk.Box(spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)
        add_btn = Gtk.Button(label="Add User")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_user)
        btn_box.append(add_btn)
        self.users_group.add(btn_box)

        root_group = Adw.PreferencesGroup(title="Root Password")
        self.root_pass_entry = Gtk.PasswordEntry()
        self.root_pass_entry.set_show_peek_icon(False)
        root_row = Adw.ActionRow(title="Root Password")
        root_row.add_suffix(self.root_pass_entry)
        root_group.add(root_row)
        page.add(root_group)

        return page

    def _rebuild_user_list(self):
        children = []
        for child in self.users_group:
            children.append(child)
        for child in children:
            if isinstance(child, Gtk.Box):
                break
            self.users_group.remove(child)

        count = int(self.state.get("USER_COUNT", 0))
        for i in range(1, count + 1):
            name = self.state.get(f"USER_{i}_NAME", f"User {i}")
            sudo = self.state.get(f"USER_{i}_SUDO", "no")
            label = f"{name} (sudo: {sudo})"
            row = Adw.ActionRow(title=label, subtitle="Click to edit or remove")
            row.connect("activated", self._on_user_row_activated, i)
            self.users_group.add(row)

    def _on_user_row_activated(self, row, idx):
        menu = Gtk.PopoverMenu.new_from_model(None)
        dialog = Gtk.AlertDialog()
        dialog.set_buttons(["Edit", "Remove", "Cancel"])
        dialog.set_message(f"Manage {self.state.get(f'USER_{idx}_NAME', f'User {idx}')}")
        dialog.choose(self.window, None, self._on_user_action_chosen, idx)

    def _on_user_action_chosen(self, dialog, result, idx):
        try:
            choice = dialog.choose_finish(result)
        except Exception:
            return
        if choice == 0:
            self._edit_user_dialog(idx)
        elif choice == 1:
            name = self.state.get(f"USER_{idx}_NAME", f"User {idx}")
            confirm = Gtk.AlertDialog()
            confirm.set_buttons(["Cancel", "Remove"])
            confirm.set_message(f"Remove {name}?")
            confirm.choose(self.window, None, lambda d, r: self._on_remove_confirmed(d, r, idx))

    def _on_remove_confirmed(self, dialog, result, idx):
        try:
            choice = dialog.choose_finish(result)
        except Exception:
            return
        if choice != 1:
            return
        count = int(self.state.get("USER_COUNT", 0))
        for i in range(idx, count):
            next_i = i + 1
            for key in ("NAME", "PASS", "SHELL", "GROUPS", "SUDO"):
                self.state[f"USER_{i}_{key}"] = self.state.get(f"USER_{next_i}_{key}", "")
        for key in ("NAME", "PASS", "SHELL", "GROUPS", "SUDO"):
            self.state.pop(f"USER_{count}_{key}", None)
        self.state["USER_COUNT"] = str(count - 1)
        self._rebuild_user_list()

    def _on_add_user(self, btn):
        count = int(self.state.get("USER_COUNT", 0))
        self._edit_user_dialog(count + 1)

    def _edit_user_dialog(self, idx):
        dialog = Gtk.Dialog(title="User Details", transient_for=self.window, modal=True)
        dialog.set_default_size(400, 350)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)
        vbox = dialog.get_content_area()
        vbox.set_spacing(10)
        vbox.set_margin_top(10); vbox.set_margin_start(10)
        vbox.set_margin_end(10); vbox.set_margin_bottom(10)

        name_entry = Gtk.Entry()
        name_entry.set_text(self.state.get(f"USER_{idx}_NAME", ""))
        vbox.append(Gtk.Label(label="Username:", xalign=0))
        vbox.append(name_entry)

        pass_entry = Gtk.PasswordEntry()
        pass_entry.set_show_peek_icon(False)
        vbox.append(Gtk.Label(label="Password:", xalign=0))
        vbox.append(pass_entry)

        shell_combo = Gtk.DropDown.new(Gtk.StringList.new(["bash", "zsh", "fish"]))
        current_shell = self.state.get(f"USER_{idx}_SHELL", "/bin/bash")
        if "zsh" in current_shell: shell_combo.set_selected(1)
        elif "fish" in current_shell: shell_combo.set_selected(2)
        else: shell_combo.set_selected(0)
        vbox.append(Gtk.Label(label="Shell:", xalign=0))
        vbox.append(shell_combo)

        vbox.append(Gtk.Label(label="Groups:", xalign=0))
        groups_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        group_names = ["wheel", "audio", "video", "storage", "lp", "network", "optical", "scanner", "users"]
        current_groups = self.state.get(f"USER_{idx}_GROUPS", "wheel audio video storage").split()
        checks = {}
        for g in group_names:
            check = Gtk.CheckButton(label=g)
            check.set_active(g in current_groups)
            checks[g] = check
            groups_box.append(check)
        vbox.append(groups_box)

        sudo_switch = Gtk.Switch()
        sudo_switch.set_active(self.state.get(f"USER_{idx}_SUDO", "yes") == "yes")
        sudo_row = Adw.ActionRow(title="Sudo access")
        sudo_row.add_suffix(sudo_switch)
        vbox.append(sudo_row)

        dialog.show()

        def on_response(d, resp):
            if resp == Gtk.ResponseType.OK:
                name = name_entry.get_text().strip()
                if not name: return
                raw_pass = pass_entry.get_text()
                hashed = ""
                if raw_pass:
                    result = subprocess.run(['openssl', 'passwd', '-6', raw_pass], capture_output=True, text=True)
                    hashed = result.stdout.strip()
                shell_vals = ["/bin/bash", "/bin/zsh", "/usr/bin/fish"]
                shell = shell_vals[shell_combo.get_selected()]
                groups = " ".join([g for g, cb in checks.items() if cb.get_active()])
                sudo = "yes" if sudo_switch.get_active() else "no"
                self.state[f"USER_{idx}_NAME"] = name
                self.state[f"USER_{idx}_PASS"] = hashed
                self.state[f"USER_{idx}_SHELL"] = shell
                self.state[f"USER_{idx}_GROUPS"] = groups
                self.state[f"USER_{idx}_SUDO"] = sudo
                count = int(self.state.get("USER_COUNT", 0))
                if idx > count: self.state["USER_COUNT"] = str(idx)
                self._rebuild_user_list()
            dialog.destroy()

        dialog.connect("response", on_response)

    def create_privilege_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Privilege & Repositories")

        self.priv_combo = Gtk.DropDown.new(Gtk.StringList.new(["sudo", "doas"]))
        row = Adw.ActionRow(title="Privilege Escalation")
        row.add_suffix(self.priv_combo)
        group.add(row)

        self.arch_repos_switch = Gtk.Switch()
        arch_row = Adw.ActionRow(title="Enable Arch Linux repositories", subtitle="Access to extra/multilib")
        arch_row.add_suffix(self.arch_repos_switch)
        group.add(arch_row)

        self.auris_switch = Gtk.Switch()
        auris_row = Adw.ActionRow(title="Enable AURIS", subtitle="Artix User Repository of Init Scripts")
        auris_row.add_suffix(self.auris_switch)
        group.add(auris_row)

        self.offline_switch = Gtk.Switch()
        off_row = Adw.ActionRow(title="Offline mode", subtitle="Cache packages for offline install")
        off_row.add_suffix(self.offline_switch)
        group.add(off_row)

        self.poweruser_switch = Gtk.Switch()
        pw_row = Adw.ActionRow(title="Power User Mode", subtitle="Source compilation")
        pw_row.add_suffix(self.poweruser_switch)
        group.add(pw_row)

        self.poweruser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.coreutils_combo = Gtk.DropDown.new(Gtk.StringList.new(["gnu", "busybox", "uutils", "artix", "custom"]))
        core_row = Adw.ActionRow(title="Coreutils")
        core_row.add_suffix(self.coreutils_combo)
        self.poweruser_box.append(core_row)

        self.keep_binary_switch = Gtk.Switch()
        self.keep_binary_switch.set_active(True)
        keep_row = Adw.ActionRow(title="Keep binary kernel as fallback")
        keep_row.add_suffix(self.keep_binary_switch)
        self.poweruser_box.append(keep_row)

        packages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.poweruser_packages = []
        for pkg in ["linux", "glibc", "busybox", "openssl", "zlib", "zstd", "mesa"]:
            check = Gtk.CheckButton(label=pkg)
            self.poweruser_packages.append(check)
            packages_box.append(check)
        self.poweruser_box.append(packages_box)
        self.poweruser_box.set_visible(False)

        self.poweruser_switch.connect("state-set", lambda sw, state: self.poweruser_box.set_visible(state))
        group.add(self.poweruser_box)
        page.add(group)
        return page

    def create_summary_page(self, install_callback):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Installation Summary")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(350)
        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.set_child(self.summary_text)
        group.add(scrolled)

        install_btn = Gtk.Button(label="Install")
        install_btn.add_css_class("suggested-action")
        install_btn.set_halign(Gtk.Align.CENTER)
        install_btn.connect("clicked", lambda b: install_callback())
        group.add(install_btn)

        page.add(group)
        return page


    def collect_state_common(self):
        if hasattr(self, 'theme_combo'):
            themes = ["ArtixForge", "Artix", "Jet Black", "Mono", "Retro"]
            idx = self.theme_combo.get_selected()
            if 0 <= idx < len(themes):
                self.state['GUM_TITLE_COLOR'], self.state['GUM_ACCENT_COLOR'] = {
                    "ArtixForge": ("212", "34"), "Artix": ("39", "117"),
                    "Jet Black": ("245", "196"), "Mono": ("250", "255"),
                    "Retro": ("3", "11"),
                }.get(themes[idx], ("212", "34"))

        if hasattr(self, 'fs_combo'):
            fs_values = ["ext4", "btrfs", "xfs", "f2fs"]
            idx = self.fs_combo.get_selected()
            if 0 <= idx < len(fs_values): self.state['FS_TYPE'] = fs_values[idx]
        if hasattr(self, 'btrfs_layout_combo'):
            layout = ["standard", "flat", "snapshot"]
            idx = self.btrfs_layout_combo.get_selected()
            if 0 <= idx < len(layout): self.state['BTRFS_LAYOUT'] = layout[idx]

        if hasattr(self, 'bl_combo'):
            artix_boot_mode = os.environ.get("ARTIX_BOOT_MODE", "uefi")
            bl_values = ["grub"] if artix_boot_mode == "bios" else ["grub", "refind", "efistub", "limine"]
            idx = self.bl_combo.get_selected()
            if 0 <= idx < len(bl_values): self.state['BOOTLOADER'] = bl_values[idx]
        if hasattr(self, 'uki_switch'):
            self.state['GENERATE_UKI'] = "yes" if self.uki_switch.get_active() else "no"

        if hasattr(self, 'kernel_combo'):
            kernels = ["linux", "linux-zen", "linux-lts", "linux-hardened", "linux-libre", "linux-cachyos-bore", "linux-bazzite-bin", "xanmod", "tkg"]
            idx = self.kernel_combo.get_selected()
            if 0 <= idx < len(kernels): self.state['KERNEL_CHOICE'] = kernels[idx]
        if hasattr(self, 'microcode_combo'):
            ucodes = ["auto", "intel-ucode", "amd-ucode", "none"]
            idx = self.microcode_combo.get_selected()
            if 0 <= idx < len(ucodes): self.state['MICROCODE_OVERRIDE'] = ucodes[idx]

        if hasattr(self, 'init_combo'):
            inits = ["openrc", "runit", "dinit", "s6"]
            idx = self.init_combo.get_selected()
            if 0 <= idx < len(inits): self.state['INIT'] = inits[idx]

        if hasattr(self, 'de_combo'):
            des = ["kde", "sonicde", "xfce4", "lxqt", "lxde", "hyprland", "sway", "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "cinnamon", "budgie", "moksha", "cosmic", "none"]
            idx = self.de_combo.get_selected()
            if 0 <= idx < len(des): self.state['WM_DE'] = des[idx]
        if hasattr(self, 'xstack_combo'):
            xs = ["xlibre", "xorg"]
            idx = self.xstack_combo.get_selected()
            if 0 <= idx < len(xs): self.state['X_STACK'] = xs[idx]
        if hasattr(self, 'dm_combo'):
            dms = ["none", "lightdm", "sddm", "soniclogin"]
            idx = self.dm_combo.get_selected()
            if 0 <= idx < len(dms): self.state['DISPLAY_MANAGER'] = dms[idx]

        if hasattr(self, 'net_combo'):
            nets = ["networkmanager", "dhcpcd+iwd", "connman", "none"]
            idx = self.net_combo.get_selected()
            if 0 <= idx < len(nets): self.state['NETWORK_STACK'] = nets[idx]
        if hasattr(self, 'audio_combo'):
            audios = ["pipewire", "pulseaudio", "none"]
            idx = self.audio_combo.get_selected()
            if 0 <= idx < len(audios): self.state['AUDIO_STACK'] = audios[idx]

        extras = []
        if hasattr(self, '_InstallerApp__extras_checkboxes'):
            for pkg, cb in self._InstallerApp__extras_checkboxes.items():
                if cb.get_active(): extras.append(pkg)
        self.state['EXTRAS'] = " ".join(extras)

        if hasattr(self, 'root_pass_entry'):
            raw = self.root_pass_entry.get_text()
            if raw:
                result = subprocess.run(['openssl', 'passwd', '-6', raw], capture_output=True, text=True)
                self.state['ROOT_PASS'] = result.stdout.strip()

        if hasattr(self, 'priv_combo'):
            self.state['PRIV_ESCALATION'] = "sudo" if self.priv_combo.get_selected() == 0 else "doas"
        if hasattr(self, 'arch_repos_switch'):
            self.state['ENABLE_ARCH_REPOS'] = "yes" if self.arch_repos_switch.get_active() else "no"
        if hasattr(self, 'auris_switch'):
            self.state['ENABLE_AURIS'] = "yes" if self.auris_switch.get_active() else "no"
        if hasattr(self, 'offline_switch'):
            self.state['ALLOW_OFFLINE'] = "yes" if self.offline_switch.get_active() else "no"
        if hasattr(self, 'poweruser_switch'):
            self.state['POWER_USER'] = "yes" if self.poweruser_switch.get_active() else "no"
            if hasattr(self, 'coreutils_combo'):
                cu = ["gnu", "busybox", "uutils", "artix", "custom"]
                self.state['COREUTILS'] = cu[self.coreutils_combo.get_selected()]
            if hasattr(self, 'keep_binary_switch'):
                self.state['KEEP_BINARY_KERNEL'] = "yes" if self.keep_binary_switch.get_active() else "no"
            if hasattr(self, 'poweruser_packages'):
                sel = [cb.get_label() for cb in self.poweruser_packages if cb.get_active()]
                self.state['POWERUSER_PACKAGES'] = " ".join(sel)

        self.state['ARTIX_BOOT_MODE'] = os.environ.get("ARTIX_BOOT_MODE", "uefi")
        self.state['GUI_MODE'] = "yes"


    def start_installation(self, mode_title):
        self.save_state()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        install_script = os.path.join(base_dir, "install")
        progress_page = ProgressPage(
            title=mode_title,
            command=[install_script, "--non-interactive"],
            state=self.state,
            cwd=base_dir,
            on_complete=self._on_install_complete
        )
        self.nav_view.push(Adw.NavigationPage(child=progress_page, title=mode_title))

    def _on_install_complete(self, success, cancelled):
        if cancelled:
            msg = "Installation cancelled by user."
            icon = "dialog-warning-symbolic"
        elif success:
            msg = "Installation completed successfully!\nYou may now reboot."
            icon = "emblem-ok-symbolic"
        else:
            log_tail = ""
            try:
                with open("/tmp/artix-installer/install.log", "r") as f:
                    lines = f.readlines()
                    cleaned = [''.join(c for c in l if c.isprintable() or c in '\n\r\t ') for l in lines[-8:]]
                    log_tail = "".join(cleaned) if cleaned else "(empty log)"
            except Exception:
                log_tail = "(could not read log)"
            msg = f"Installation failed.\n\nLast log lines:\n{log_tail}"
            icon = "dialog-error-symbolic"

        status_page = Adw.StatusPage()
        status_page.set_title("ArtixForge")
        status_page.set_description(msg)
        if icon: status_page.set_icon_name(icon)
        self.nav_view.push(Adw.NavigationPage(child=status_page, title="Result"))