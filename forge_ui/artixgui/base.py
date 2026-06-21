#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import os
import subprocess
from gi.repository import Gtk, Adw, Gdk, GLib
from ..backends.gui import ProgressWindow
from ..theme import get_colors, ACCENT_COLORS


class BaseWindow:
    def __init__(self, state_file, state, title="ArtixForge", app=None):
        self.state_file = state_file
        self.state = state
        self.pages = []
        self.current_page = 0
        self._conditional_pages = {}
        self._users_page = None

        self.app = app or Gtk.Application.get_default()

        title_color, accent_color = get_colors()
        self.title_color = title_color
        self.accent_color = accent_color

        self.window = Gtk.Window(title=title)
        self.window.set_default_size(680, 420)
        self.window.connect("close-request", lambda *_: self._quit())

        self._apply_theme()

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_vbox.set_margin_top(10)
        main_vbox.set_margin_bottom(10)
        main_vbox.set_margin_start(10)
        main_vbox.set_margin_end(10)

        # Header with logo and title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_box.set_halign(Gtk.Align.CENTER)
        main_vbox.append(header_box)

        logo_path = os.path.join(os.path.dirname(__file__), "media", "artix-logo.png")
        has_logo = os.path.exists(logo_path)

        if has_logo:
            try:
                logo = Gtk.Picture.new_for_filename(logo_path)
                logo.set_size_request(48, 48)
                logo.set_margin_end(10)
                header_box.append(logo)
            except Exception:
                pass

        header = Gtk.Label()
        header.set_markup('<span size="large" weight="bold">ArtixForge Installer</span>')
        header_box.append(header)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.stack.set_vexpand(True)
        main_vbox.append(self.stack)

        nav_box = Gtk.Box(spacing=10)
        nav_box.set_halign(Gtk.Align.CENTER)
        nav_box.set_margin_top(10)

        self.back_btn = Gtk.Button(label="Back")
        self.back_btn.connect("clicked", self.on_back)
        self.back_btn.set_sensitive(False)
        nav_box.append(self.back_btn)

        self.next_btn = Gtk.Button(label="Next")
        self.next_btn.connect("clicked", self.on_next)
        self.next_btn.add_css_class("suggested-action")
        nav_box.append(self.next_btn)

        main_vbox.append(nav_box)

        # Background watermark + header logo
        if has_logo:
            overlay = Gtk.Overlay()
            overlay.set_child(main_vbox)
            bg_logo = Gtk.Picture.new_for_filename(logo_path)
            bg_logo.set_opacity(0.15)
            bg_logo.set_halign(Gtk.Align.CENTER)
            bg_logo.set_valign(Gtk.Align.CENTER)
            bg_logo.set_can_shrink(True)
            overlay.add_overlay(bg_logo)
            self.window.set_child(overlay)
        else:
            self.window.set_child(main_vbox)

        self._loop = None

    def _apply_theme(self):
        light = (self.state.get("GUI_BACKGROUND", "black") == "white")
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

    def add_page(self, title, page, conditional=None):
        page.set_visible(True)
        self.stack.add_titled(page, title, title)
        self.pages.append(page)
        if conditional:
            self._conditional_pages[title] = (len(self.pages) - 1, conditional)

    def add_revealer_page(self, title, content, conditional=None):
        revealer = Gtk.Revealer()
        revealer.set_child(content)
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        revealer.set_transition_duration(300)
        revealer.set_reveal_child(True)
        self.add_page(title, revealer, conditional)

    def _update_conditional_pages(self):
        for title, (idx, condition) in self._conditional_pages.items():
            visible = condition()
            page = self.pages[idx]
            if isinstance(page, Gtk.Revealer):
                page.set_reveal_child(visible)
            else:
                page.set_visible(visible)
        self.update_nav_buttons()

    def _set_page_visible(self, page_idx, visible):
        """Show or hide a stack child (used by PowerUserWindow)."""
        if page_idx is None or page_idx >= len(self.pages):
            return
        self.pages[page_idx].set_visible(visible)

    def update_nav_buttons(self):
        self.back_btn.set_sensitive(self.current_page > 0)
        if self.current_page == len(self.pages) - 1:
            self.next_btn.set_label("Install")
        else:
            self.next_btn.set_label("Next")

    def on_back(self, widget):
        if self.current_page > 0:
            self.current_page -= 1
            while self.current_page > 0:
                page = self.pages[self.current_page]
                if isinstance(page, Gtk.Revealer) and not page.get_reveal_child():
                    self.current_page -= 1
                elif not isinstance(page, Gtk.Revealer) and not page.get_visible():
                    self.current_page -= 1
                else:
                    break
            self._show_current_page()

    def on_next(self, widget):
        if self.current_page < len(self.pages) - 1:
            if hasattr(self, '_users_page') and self.pages[self.current_page] is self._users_page:
                if not self._validate_passwords():
                    return
            self.current_page += 1
            while self.current_page < len(self.pages):
                page = self.pages[self.current_page]
                if isinstance(page, Gtk.Revealer) and not page.get_reveal_child():
                    self.current_page += 1
                elif not isinstance(page, Gtk.Revealer) and not page.get_visible():
                    self.current_page += 1
                else:
                    break
            if self.current_page >= len(self.pages):
                self.current_page = len(self.pages) - 1
            self._show_current_page()
        else:
            if not self._validate_passwords():
                return
            self.start_installation()

    def _show_current_page(self):
        self.stack.set_visible_child(self.pages[self.current_page])
        self.update_nav_buttons()
        if hasattr(self, 'update_summary') and self.pages[self.current_page] is self.pages[-1]:
            self.update_summary()

    def _validate_passwords(self):
        if hasattr(self, 'user_pass_entry') and hasattr(self, 'user_confirm_entry'):
            if self.user_pass_entry.get_text() != self.user_confirm_entry.get_text():
                dialog = Gtk.MessageDialog(
                    transient_for=self.window,
                    modal=True,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="User passwords do not match. Please correct them before continuing."
                )
                dialog.connect("response", lambda d, r: d.destroy())
                dialog.show()
                return False
        if hasattr(self, 'root_pass_entry') and hasattr(self, 'root_confirm_entry'):
            if self.root_pass_entry.get_text() != self.root_confirm_entry.get_text():
                dialog = Gtk.MessageDialog(
                    transient_for=self.window,
                    modal=True,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="Root passwords do not match. Please correct them before continuing."
                )
                dialog.connect("response", lambda d, r: d.destroy())
                dialog.show()
                return False
        return True

    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                for key, value in self.state.items():
                    f.write(f'{key}="{value}"\n')
        except Exception as e:
            print(f"Error saving state: {e}")

    def run_installer(self):
        self.save_state()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        install_script = os.path.join(base_dir, "install")

        self.window.hide()

        progress = ProgressWindow(
            {"title": "Installing ArtixForge",
             "command": [install_script, "--non-interactive"],
             "state": self.state},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()

        if result.get("cancelled"):
            dialog = Gtk.MessageDialog(
                transient_for=None,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Installation cancelled by user."
            )
        elif result.get("result") == "success":
            dialog = Gtk.MessageDialog(
                transient_for=None,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Installation completed successfully!"
            )
        else:
            log_tail = ""
            try:
                with open("/tmp/artix-installer/install.log", "r") as f:
                    lines = f.readlines()
                    cleaned = [''.join(c for c in l if c.isprintable() or c in '\n\r\t ') for l in lines[-8:]]
                    log_tail = "".join(cleaned) if cleaned else "(empty log)"
            except Exception:
                log_tail = "(could not read log)"
            dialog = Gtk.MessageDialog(
                transient_for=None,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Installation failed.\n\nLast log lines:\n{log_tail}"
            )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()
        dialog_loop = GLib.MainLoop()
        dialog.connect("response", lambda d, r: dialog_loop.quit())
        dialog_loop.run()
        self._quit()

    def start_installation(self):
        self.run_installer()

    def run(self):
        self._update_conditional_pages()
        self._show_current_page()
        self.window.show()
        self._loop = GLib.MainLoop()
        self.window.connect("destroy", lambda *_: self._loop.quit())
        self._loop.run()
        self._loop = None
        return self.state

    def _quit(self):
        if self._loop:
            self._loop.quit()
        self.window.destroy()


class CommonPages:
    def _init_common_pages(self):
        self.__extras_notebook = None
        self.__extras_checkboxes = {}
        self._users_page = None

    def create_welcome_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

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
        sysinfo.set_justify(Gtk.Justification.LEFT)
        sysinfo.set_margin_top(10)
        box.append(sysinfo)

        desc = Gtk.Label()
        desc.set_text("This installer will guide you through installing Artix Linux.\n\nPress Next to begin.")
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_margin_top(10)
        box.append(desc)

        return box

    def create_theme_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Select Theme</span>')
        box.append(label)

        themes = ["ArtixForge", "Artix", "Jet Black", "Mono", "Retro"]
        self.theme_combo = Gtk.DropDown.new(Gtk.StringList.new(themes))
        self.theme_combo.set_selected(0)
        box.append(self.theme_combo)

        preview = Gtk.Label()
        preview.set_markup('<span foreground="#c678dd" weight="bold">This is how titles will look</span>')
        box.append(preview)

        def on_theme_changed(dropdown, _param):
            idx = dropdown.get_selected()
            if 0 <= idx < len(themes):
                theme = themes[idx]
                colors = {
                    "ArtixForge": ("#c678dd", 34),
                    "Artix": ("#61afef", 117),
                    "Jet Black": ("#928374", 196),
                    "Mono": ("#a89984", 255),
                    "Retro": ("#d19a66", 11),
                }
                title_color, accent_code = colors.get(theme, ("#c678dd", 34))
                preview.set_markup(f'<span foreground="{title_color}" weight="bold">This is how titles will look</span>')
                style_manager = Adw.StyleManager.get_default()
                accent_tuple = ACCENT_COLORS.get(accent_code)
                if accent_tuple:
                    style_manager.set_accent_color(Adw.AccentColor(*accent_tuple))

        self.theme_combo.connect("notify::selected", on_theme_changed)

        self.bg_check = Gtk.CheckButton(label="Use white background")
        self.bg_check.set_active(self.state.get("GUI_BACKGROUND", "black") == "white")
        self.bg_check.connect("toggled", self.on_bg_toggled)
        box.append(self.bg_check)

        return box

    def on_bg_toggled(self, check):
        self.state["GUI_BACKGROUND"] = "white" if check.get_active() else "black"
        self._apply_theme()

    def create_filesystem_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label(label="Select filesystem:", xalign=0)
        box.append(label)

        self.fs_combo = Gtk.DropDown.new(Gtk.StringList.new(["ext4", "btrfs", "xfs", "f2fs"]))
        box.append(self.fs_combo)

        self.btrfs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btrfs_label = Gtk.Label(label="BTRFS Layout:", xalign=0)
        self.btrfs_box.append(btrfs_label)
        self.btrfs_combo = Gtk.DropDown.new(Gtk.StringList.new(["standard", "flat", "snapshot"]))
        self.btrfs_box.append(self.btrfs_combo)
        box.append(self.btrfs_box)
        self.btrfs_box.set_visible(False)

        def on_fs_changed(dropdown, _param):
            idx = dropdown.get_selected()
            self.btrfs_box.set_visible(idx == 1)

        self.fs_combo.connect("notify::selected", on_fs_changed)
        return box

    def create_bootloader_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label(label="Select bootloader:", xalign=0)
        box.append(label)
        self.bl_combo = Gtk.DropDown.new(Gtk.StringList.new(["grub", "refind", "efistub", "limine"]))
        box.append(self.bl_combo)

        self.uki_check = Gtk.CheckButton(label="Generate UKI (Unified Kernel Image)")
        box.append(self.uki_check)

        return box

    def create_kernel_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label(label="Select kernel:", xalign=0)
        box.append(label)
        self.kernel_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "linux", "linux-zen", "linux-lts", "linux-hardened",
            "linux-libre", "linux-cachyos-bore", "linux-bazzite-bin",
            "xanmod", "tkg"
        ]))
        box.append(self.kernel_combo)

        microcode_label = Gtk.Label(label="Microcode:", xalign=0)
        box.append(microcode_label)
        self.microcode_combo = Gtk.DropDown.new(Gtk.StringList.new(["auto", "intel-ucode", "amd-ucode", "none"]))
        box.append(self.microcode_combo)

        return box

    def create_init_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label(label="Select init system:", xalign=0)
        box.append(label)
        self.init_combo = Gtk.DropDown.new(Gtk.StringList.new(["openrc", "runit", "dinit", "s6"]))
        box.append(self.init_combo)

        return box

    def create_desktop_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label(label="Select desktop environment / window manager:", xalign=0)
        box.append(label)
        self.de_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "kde", "sonicde", "xfce4", "lxqt", "lxde", "hyprland", "sway",
            "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"
        ]))
        box.append(self.de_combo)

        xstack_label = Gtk.Label(label="Display stack:", xalign=0)
        box.append(xstack_label)
        self.xstack_combo = Gtk.DropDown.new(Gtk.StringList.new(["xlibre", "xorg"]))
        box.append(self.xstack_combo)

        dm_label = Gtk.Label(label="Display manager:", xalign=0)
        box.append(dm_label)
        self.dm_combo = Gtk.DropDown.new(Gtk.StringList.new(["none", "lightdm", "sddm", "soniclogin"]))
        box.append(self.dm_combo)

        return box

    def create_network_audio_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        net_label = Gtk.Label(label="Network stack:", xalign=0)
        box.append(net_label)
        self.net_combo = Gtk.DropDown.new(Gtk.StringList.new(["networkmanager", "dhcpcd+iwd", "connman", "none"]))
        box.append(self.net_combo)

        audio_label = Gtk.Label(label="Audio stack:", xalign=0)
        box.append(audio_label)
        self.audio_combo = Gtk.DropDown.new(Gtk.StringList.new(["pipewire", "pulseaudio", "none"]))
        box.append(self.audio_combo)

        return box

    def create_extras_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        shell_label = Gtk.Label(label="Select user shell:", xalign=0)
        box.append(shell_label)
        self.shell_combo = Gtk.DropDown.new(Gtk.StringList.new(["bash", "zsh", "fish"]))
        box.append(self.shell_combo)

        extras_label = Gtk.Label(label="Extra packages:", xalign=0)
        box.append(extras_label)

        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)

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

        self.__extras_checkboxes = {}
        self.__extras_notebook = notebook

        for cat_name, pkgs in categories.items():
            page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            page_box.set_margin_start(10)
            page_box.set_margin_top(10)

            for pkg in pkgs:
                check = Gtk.CheckButton(label=pkg)
                page_box.append(check)
                self.__extras_checkboxes[pkg] = check

            select_all = Gtk.Button(label=f"Select All {cat_name}")
            select_all.connect("clicked", self.on_select_all, (cat_name, pkgs))
            page_box.append(select_all)

            notebook.append_page(page_box, Gtk.Label(label=cat_name))

        # Search tab
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        search_box.set_margin_start(10)
        search_box.set_margin_top(10)

        search_entry = Gtk.Entry()
        search_entry.set_placeholder_text("Type to search packages...")
        search_box.append(search_entry)

        search_scroll = Gtk.ScrolledWindow()
        search_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        search_scroll.set_min_content_height(200)
        search_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        search_scroll.set_child(search_results_box)
        search_box.append(search_scroll)

        def on_search_changed(entry):
            for child in list(search_results_box):
                search_results_box.remove(child)
            query = entry.get_text().strip()
            if len(query) < 2:
                return
            try:
                result = subprocess.run(
                    ["pacman", "-Sl", "world", "galaxy"],
                    capture_output=True, text=True, timeout=15
                )
                pkg_set = set()
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            pkg_set.add(parts[1])
                safe_filter = [
                    "linux-", "systemd", "plasma-", "grub", "mkinitcpio",
                    "-openrc", "-runit", "-dinit", "-s6", "sddm", "lightdm",
                    "gdm", "xorg-", "xlibre-", "wayland", "hyprland", "sway",
                    "niri", "pipewire", "pulseaudio", "networkmanager",
                    "connman", "dhcpcd", "efibootmgr", "filesystem", "pacman",
                    "bash", "coreutils", "util-linux"
                ]
                matches = sorted([
                    p for p in pkg_set
                    if query.lower() in p.lower()
                    and not any(f in p.lower() for f in safe_filter)
                ])[:50]
                for pkg in matches:
                    check = Gtk.CheckButton(label=pkg)
                    search_results_box.append(check)
                    self.__extras_checkboxes[pkg] = check
            except Exception:
                pass

        search_entry.connect("changed", on_search_changed)
        notebook.append_page(search_box, Gtk.Label(label="Search"))

        box.append(notebook)
        return box

    def on_select_all(self, widget, data):
        cat_name, pkgs = data
        for pkg in pkgs:
            if pkg in self.__extras_checkboxes:
                self.__extras_checkboxes[pkg].set_active(True)

    def create_users_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        hostname_label = Gtk.Label(label="Hostname:", xalign=0)
        box.append(hostname_label)
        self.hostname_entry = Gtk.Entry()
        self.hostname_entry.set_text("artix")
        box.append(self.hostname_entry)

        tz_label = Gtk.Label(label="Timezone:", xalign=0)
        box.append(tz_label)
        self.timezone_entry = Gtk.Entry()
        self.timezone_entry.set_text("Europe/Belgrade")
        box.append(self.timezone_entry)

        locale_label = Gtk.Label(label="Locale:", xalign=0)
        box.append(locale_label)
        self.locale_entry = Gtk.Entry()
        self.locale_entry.set_text("en_US.UTF-8")
        box.append(self.locale_entry)

        keymap_label = Gtk.Label(label="Keyboard layout:", xalign=0)
        box.append(keymap_label)
        self.keymap_entry = Gtk.Entry()
        self.keymap_entry.set_text("us")
        box.append(self.keymap_entry)

        username_label = Gtk.Label(label="Username:", xalign=0)
        box.append(username_label)
        self.username_entry = Gtk.Entry()
        self.username_entry.set_text("artix")
        box.append(self.username_entry)

        user_pass_label = Gtk.Label(label="User Password:", xalign=0)
        box.append(user_pass_label)
        self.user_pass_entry = Gtk.PasswordEntry()
        self.user_pass_entry.set_show_peek_icon(False)
        box.append(self.user_pass_entry)

        user_confirm_label = Gtk.Label(label="Confirm User Password:", xalign=0)
        box.append(user_confirm_label)
        self.user_confirm_entry = Gtk.PasswordEntry()
        self.user_confirm_entry.set_show_peek_icon(False)
        box.append(self.user_confirm_entry)

        root_pass_label = Gtk.Label(label="Root Password:", xalign=0)
        box.append(root_pass_label)
        self.root_pass_entry = Gtk.PasswordEntry()
        self.root_pass_entry.set_show_peek_icon(False)
        box.append(self.root_pass_entry)

        root_confirm_label = Gtk.Label(label="Confirm Root Password:", xalign=0)
        box.append(root_confirm_label)
        self.root_confirm_entry = Gtk.PasswordEntry()
        self.root_confirm_entry.set_show_peek_icon(False)
        box.append(self.root_confirm_entry)

        self._users_page = box
        return box

    def create_privilege_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        priv_label = Gtk.Label(label="Privilege escalation:", xalign=0)
        box.append(priv_label)
        self.priv_combo = Gtk.DropDown.new(Gtk.StringList.new(["sudo", "doas"]))
        box.append(self.priv_combo)

        self.arch_repos_check = Gtk.CheckButton(label="Enable Arch Linux repositories")
        box.append(self.arch_repos_check)
        self.auris_check = Gtk.CheckButton(label="Enable AURIS (Artix User Repository of Init Scripts)")
        box.append(self.auris_check)
        self.offline_check = Gtk.CheckButton(label="Enable offline installation mode (cached packages)")
        box.append(self.offline_check)

        self.poweruser_check = Gtk.CheckButton(label="Enable Power User Mode (source compilation)")
        box.append(self.poweruser_check)

        self.poweruser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.poweruser_box.set_margin_start(20)

        coreutils_label = Gtk.Label(label="Coreutils:", xalign=0)
        self.poweruser_box.append(coreutils_label)
        self.coreutils_combo = Gtk.DropDown.new(Gtk.StringList.new(["gnu", "busybox", "uutils", "artix", "custom"]))
        self.poweruser_box.append(self.coreutils_combo)

        keep_binary_label = Gtk.Label(label="Keep binary kernel as fallback:", xalign=0)
        self.poweruser_box.append(keep_binary_label)
        self.keep_binary_check = Gtk.CheckButton(label="Yes, keep binary kernel")
        self.keep_binary_check.set_active(True)
        self.poweruser_box.append(self.keep_binary_check)

        packages_label = Gtk.Label(label="Packages to build from source:", xalign=0)
        self.poweruser_box.append(packages_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(150)
        packages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        packages = ["linux", "glibc", "busybox", "openssl", "zlib", "zstd", "mesa"]
        self.poweruser_packages = []
        for pkg in packages:
            check = Gtk.CheckButton(label=pkg)
            self.poweruser_packages.append(check)
            packages_box.append(check)
        scroll.set_child(packages_box)
        self.poweruser_box.append(scroll)

        box.append(self.poweruser_box)
        self.poweruser_box.set_visible(False)
        self.poweruser_check.connect("toggled", self.on_poweruser_toggled)

        return box

    def on_poweruser_toggled(self, check):
        self.poweruser_box.set_visible(check.get_active())
        self._update_conditional_pages()

    def create_summary_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Installation Summary</span>')
        box.append(label)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(400)
        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.set_child(self.summary_text)
        box.append(scrolled)

        self.stack.connect("notify::visible-child", self.on_page_changed)
        return box

    def on_page_changed(self, stack, param):
        if stack.get_visible_child() == self.pages[-1]:
            self.update_summary()

    def update_summary(self):
        self.collect_state_common()
        summary = "Installation Summary:\n\n"
        for key, value in sorted(self.state.items()):
            if key not in ['LUKS_PASS', 'USER_PASS', 'ROOT_PASS']:
                summary += f"{key}: {value}\n"
        warnings = []
        if self.state.get('POWER_USER') == "yes" and "glibc" in self.state.get('POWERUSER_PACKAGES', ""):
            warnings.append("glibc from source is DANGEROUS – a miscompilation breaks everything")
        if self.state.get('FS_TYPE') == "zfs":
            warnings.append("ZFS is experimental – DKMS rebuilds may be required")
        if self.state.get('BOOTLOADER') == "efistub" and self.state.get('USE_LUKS') == "yes":
            warnings.append("EFIStub + LUKS: ensure initramfs includes encrypt hook")
        if warnings:
            summary += "\n\nSanity Warnings:\n" + "\n".join(warnings)
        self.summary_text.get_buffer().set_text(summary)

    def collect_state_common(self):
        if not self._validate_passwords():
            return False

        if hasattr(self, 'theme_combo'):
            themes = ["ArtixForge", "Artix", "Jet Black", "Mono", "Retro"]
            idx = self.theme_combo.get_selected()
            if 0 <= idx < len(themes):
                theme = themes[idx]
                colors = {
                    "ArtixForge": ("212", "34"),
                    "Artix": ("39", "117"),
                    "Jet Black": ("245", "196"),
                    "Mono": ("250", "255"),
                    "Retro": ("3", "11"),
                }
                tc, ac = colors.get(theme, ("212", "34"))
                self.state['GUM_TITLE_COLOR'] = tc
                self.state['GUM_ACCENT_COLOR'] = ac

        if hasattr(self, 'bg_check'):
            self.state['GUI_BACKGROUND'] = "white" if self.bg_check.get_active() else "black"

        if hasattr(self, 'fs_combo'):
            fs_values = ["ext4", "btrfs", "xfs", "f2fs"]
            idx = self.fs_combo.get_selected()
            if 0 <= idx < len(fs_values):
                self.state['FS_TYPE'] = fs_values[idx]

        if hasattr(self, 'btrfs_combo') and self.state.get('FS_TYPE') == "btrfs":
            btrfs_values = ["standard", "flat", "snapshot"]
            idx = self.btrfs_combo.get_selected()
            if 0 <= idx < len(btrfs_values):
                self.state['BTRFS_LAYOUT'] = btrfs_values[idx]

        if hasattr(self, 'bl_combo'):
            bl_values = ["grub", "refind", "efistub", "limine"]
            idx = self.bl_combo.get_selected()
            if 0 <= idx < len(bl_values):
                self.state['BOOTLOADER'] = bl_values[idx]

        if hasattr(self, 'uki_check'):
            self.state['GENERATE_UKI'] = "yes" if self.uki_check.get_active() else "no"

        if hasattr(self, 'kernel_combo'):
            kernel_values = ["linux", "linux-zen", "linux-lts", "linux-hardened",
                             "linux-libre", "linux-cachyos-bore", "linux-bazzite-bin",
                             "xanmod", "tkg"]
            idx = self.kernel_combo.get_selected()
            if 0 <= idx < len(kernel_values):
                self.state['KERNEL_CHOICE'] = kernel_values[idx]

        if hasattr(self, 'microcode_combo'):
            ucode_values = ["auto", "intel-ucode", "amd-ucode", "none"]
            idx = self.microcode_combo.get_selected()
            if 0 <= idx < len(ucode_values):
                self.state['MICROCODE_OVERRIDE'] = ucode_values[idx]

        if hasattr(self, 'init_combo'):
            init_values = ["openrc", "runit", "dinit", "s6"]
            idx = self.init_combo.get_selected()
            if 0 <= idx < len(init_values):
                self.state['INIT'] = init_values[idx]

        if hasattr(self, 'de_combo'):
            de_values = ["kde", "sonicde", "xfce4", "lxqt", "lxde", "hyprland", "sway",
                         "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]
            idx = self.de_combo.get_selected()
            if 0 <= idx < len(de_values):
                self.state['WM_DE'] = de_values[idx]

        if hasattr(self, 'xstack_combo'):
            xs_values = ["xlibre", "xorg"]
            idx = self.xstack_combo.get_selected()
            if 0 <= idx < len(xs_values):
                self.state['X_STACK'] = xs_values[idx]

        if hasattr(self, 'dm_combo'):
            dm_values = ["none", "lightdm", "sddm", "soniclogin"]
            idx = self.dm_combo.get_selected()
            if 0 <= idx < len(dm_values):
                self.state['DISPLAY_MANAGER'] = dm_values[idx]

        if hasattr(self, 'net_combo'):
            net_values = ["networkmanager", "dhcpcd+iwd", "connman", "none"]
            idx = self.net_combo.get_selected()
            if 0 <= idx < len(net_values):
                self.state['NETWORK_STACK'] = net_values[idx]

        if hasattr(self, 'audio_combo'):
            audio_values = ["pipewire", "pulseaudio", "none"]
            idx = self.audio_combo.get_selected()
            if 0 <= idx < len(audio_values):
                self.state['AUDIO_STACK'] = audio_values[idx]

        if hasattr(self, 'shell_combo'):
            shell_values = ["bash", "zsh", "fish"]
            idx = self.shell_combo.get_selected()
            if 0 <= idx < len(shell_values):
                self.state['USER_SHELL'] = shell_values[idx]

        extras = []
        if hasattr(self, '_CommonPages__extras_checkboxes'):
            cb_dict = self._CommonPages__extras_checkboxes
            if isinstance(cb_dict, dict):
                for pkg, cb in cb_dict.items():
                    if isinstance(cb, Gtk.CheckButton) and cb.get_active():
                        extras.append(pkg)
        self.state['EXTRAS'] = " ".join(extras)

        if hasattr(self, 'hostname_entry'):
            self.state['HOSTNAME'] = self.hostname_entry.get_text()
        if hasattr(self, 'timezone_entry'):
            self.state['TIMEZONE'] = self.timezone_entry.get_text()
        if hasattr(self, 'locale_entry'):
            self.state['LOCALE'] = self.locale_entry.get_text()
        if hasattr(self, 'keymap_entry'):
            self.state['KEYMAP'] = self.keymap_entry.get_text()
        if hasattr(self, 'username_entry'):
            self.state['USER_NAME'] = self.username_entry.get_text()
        if hasattr(self, 'user_pass_entry'):
            self.state['USER_PASS'] = self.user_pass_entry.get_text()
        if hasattr(self, 'root_pass_entry'):
            self.state['ROOT_PASS'] = self.root_pass_entry.get_text()

        if hasattr(self, 'priv_combo'):
            priv_values = ["sudo", "doas"]
            idx = self.priv_combo.get_selected()
            if 0 <= idx < len(priv_values):
                self.state['PRIV_ESCALATION'] = priv_values[idx]

        if hasattr(self, 'arch_repos_check'):
            self.state['ENABLE_ARCH_REPOS'] = "yes" if self.arch_repos_check.get_active() else "no"
        if hasattr(self, 'auris_check'):
            self.state['ENABLE_AURIS'] = "yes" if self.auris_check.get_active() else "no"
        if hasattr(self, 'offline_check'):
            self.state['ALLOW_OFFLINE'] = "yes" if self.offline_check.get_active() else "no"

        if hasattr(self, 'poweruser_check'):
            self.state['POWER_USER'] = "yes" if self.poweruser_check.get_active() else "no"
            if hasattr(self, 'coreutils_combo') and self.poweruser_check.get_active():
                cu_values = ["gnu", "busybox", "uutils", "artix", "custom"]
                idx = self.coreutils_combo.get_selected()
                if 0 <= idx < len(cu_values):
                    self.state['COREUTILS'] = cu_values[idx]
            if hasattr(self, 'keep_binary_check'):
                self.state['KEEP_BINARY_KERNEL'] = "yes" if self.keep_binary_check.get_active() else "no"
            if hasattr(self, 'poweruser_packages'):
                selected = [cb.get_label() for cb in self.poweruser_packages if cb.get_active()]
                self.state['POWERUSER_PACKAGES'] = " ".join(selected)

        self.state['GUI_MODE'] = "yes"
        return True