#!/usr/bin/env python3
import os
import subprocess
from gi.repository import Gtk, Gdk
from ..backends.gui import ProgressWindow
from ..theme import get_colors, get_global_css


class BaseWindow:
    def __init__(self, state_file, state, title="ArtixForge"):
        self.state_file = state_file
        self.state = state
        self.pages = []
        self.current_page = 0
        
        title_color, accent_color = get_colors()
        self.title_color = title_color
        self.accent_color = accent_color
        
        self.window = Gtk.Window(title=title)
        self.window.set_default_size(900, 700)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Background colour
        bg = self.state.get("GUI_BACKGROUND", "black")
        if bg == "white":
            self.window.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))
        else:
            self.window.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
        
        # Global styling
        css = get_global_css(self.title_color, self.accent_color)
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Main vertical box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_vbox.set_border_width(10)
        self.window.add(main_vbox)
        
        # Header
        header = Gtk.Label()
        header.set_markup('<span size="large" weight="bold">ArtixForge Installer</span>')
        main_vbox.pack_start(header, False, False, 0)
        
        # Stack for pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        main_vbox.pack_start(self.stack, True, True, 0)
        
        # Navigation buttons
        nav_box = Gtk.Box(spacing=10)
        nav_box.set_halign(Gtk.Align.CENTER)
        nav_box.set_margin_top(10)
        
        self.back_btn = Gtk.Button(label="Back")
        self.back_btn.connect("clicked", self.on_back)
        self.back_btn.set_sensitive(False)
        nav_box.pack_start(self.back_btn, False, False, 0)
        
        self.next_btn = Gtk.Button(label="Next")
        self.next_btn.connect("clicked", self.on_next)
        nav_box.pack_start(self.next_btn, False, False, 0)
        
        main_vbox.pack_start(nav_box, False, False, 0)
    
    def add_page(self, title, page):
        self.stack.add_titled(page, title, title)
        self.pages.append(page)
    
    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            tmpfile = f"/tmp/artix-state-{os.getpid()}.tmp"
            with open(tmpfile, 'w') as f:
                for key, value in self.state.items():
                    f.write(f'{key}="{value}"\n')
            subprocess.run(['sudo', 'cp', tmpfile, self.state_file], check=True)
            subprocess.run(['sudo', 'chown', 'root:root', self.state_file], check=True)
            subprocess.run(['shred', '-u', tmpfile], check=True)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def run_installer(self):
        self.save_state()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        install_script = os.path.join(base_dir, "..", "install")
        
        self.window.hide()
        
        progress = ProgressWindow(
            {"title": "Installing ArtixForge", "command": ["sudo", install_script, "--non-interactive"]},
            title_color=self.title_color, accent_color=self.accent_color
        )
        result = progress.run()
        
        if result.get("cancelled"):
            dialog = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                message_format="Installation cancelled by user."
            )
        elif result.get("result") == "success":
            dialog = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                message_format="Installation completed successfully!"
            )
        else:
            dialog = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="Installation failed. Check logs for details."
            )
        dialog.run()
        dialog.destroy()
        Gtk.main_quit()
    
    def on_back(self, widget):
        if self.current_page > 0:
            self.current_page -= 1
            self.stack.set_visible_child(self.pages[self.current_page])
            self.update_nav_buttons()
    
    def on_next(self, widget):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.stack.set_visible_child(self.pages[self.current_page])
            self.update_nav_buttons()
        else:
            self.start_installation()
    
    def update_nav_buttons(self):
        self.back_btn.set_sensitive(self.current_page > 0)
        if self.current_page == len(self.pages) - 1:
            self.next_btn.set_label("Install")
        else:
            self.next_btn.set_label("Next")
    
    def start_installation(self):
        self.run_installer()
    
    def run(self):
        self.stack.set_visible_child(self.pages[0])
        self.update_nav_buttons()
        self.window.show_all()
        Gtk.main()
        return self.state


class CommonPages:    
    def __init_common_pages(self):
        self.__extras_notebook = None
        self.__extras_checkboxes = {}
    
    def create_welcome_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        
        label = Gtk.Label()
        label.set_markup('<span size="x-large" weight="bold">Welcome to ArtixForge</span>')
        box.pack_start(label, False, False, 0)
        
        desc = Gtk.Label()
        desc.set_text("This installer will guide you through installing Artix Linux.\n\nPress Next to begin.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 10)
        
        return box
    
    def create_theme_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Select Theme</span>')
        box.pack_start(label, False, False, 0)
        
        themes = ["Gentoo", "Artix", "Jet Black", "Mono", "Retro"]
        self.theme_combo = Gtk.ComboBoxText()
        for theme in themes:
            self.theme_combo.append_text(theme)
        self.theme_combo.set_active(0)
        box.pack_start(self.theme_combo, False, False, 10)
        
        preview = Gtk.Label()
        preview.set_markup('<span foreground="#c678dd" weight="bold">This is how titles will look</span>')
        box.pack_start(preview, False, False, 5)
        
        def on_theme_changed(combo):
            theme = combo.get_active_text()
            colors = {
                "Gentoo": ("#c678dd", "#98c379"),
                "Artix": ("#61afef", "#56b6c2"),
                "Jet Black": ("#928374", "#e06c75"),
                "Mono": ("#a89984", "#ffffff"),
                "Retro": ("#d19a66", "#e5c07b"),
            }
            title_color, _ = colors.get(theme, ("#c678dd", "#98c379"))
            preview.set_markup(f'<span foreground="{title_color}" weight="bold">This is how titles will look</span>')
        
        self.theme_combo.connect("changed", on_theme_changed)
        
        return box
    
    def create_filesystem_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label(label="Select filesystem:", xalign=0)
        box.pack_start(label, False, False, 0)
        
        fs_store = Gtk.ListStore(str)
        for fs in ["ext4", "btrfs", "xfs", "f2fs", "exfat", "zfs"]:
            fs_store.append([fs])
        
        self.fs_combo = Gtk.ComboBox.new_with_model(fs_store)
        renderer_text = Gtk.CellRendererText()
        self.fs_combo.pack_start(renderer_text, True)
        self.fs_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.fs_combo, False, False, 0)
        
        self.btrfs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btrfs_label = Gtk.Label(label="BTRFS Layout:", xalign=0)
        self.btrfs_box.pack_start(btrfs_label, False, False, 0)
        
        btrfs_store = Gtk.ListStore(str)
        for layout in ["standard", "flat", "snapshot"]:
            btrfs_store.append([layout])
        
        self.btrfs_combo = Gtk.ComboBox.new_with_model(btrfs_store)
        renderer_text = Gtk.CellRendererText()
        self.btrfs_combo.pack_start(renderer_text, True)
        self.btrfs_combo.add_attribute(renderer_text, "text", 0)
        self.btrfs_box.pack_start(self.btrfs_combo, False, False, 0)
        
        box.pack_start(self.btrfs_box, False, False, 0)
        self.btrfs_box.set_no_show_all(True)
        self.btrfs_box.hide()
        
        self.fs_combo.connect("changed", self.on_fs_changed)
        
        return box
    
    def on_fs_changed(self, combo):
        iter = combo.get_active_iter()
        if iter:
            fs = combo.get_model()[iter][0]
            if fs == "btrfs":
                self.btrfs_box.show_all()
            else:
                self.btrfs_box.hide()
    
    def create_bootloader_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label(label="Select bootloader:", xalign=0)
        box.pack_start(label, False, False, 0)
        
        bl_store = Gtk.ListStore(str)
        for bl in ["grub", "refind", "efistub", "limine"]:
            bl_store.append([bl])
        
        self.bl_combo = Gtk.ComboBox.new_with_model(bl_store)
        renderer_text = Gtk.CellRendererText()
        self.bl_combo.pack_start(renderer_text, True)
        self.bl_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.bl_combo, False, False, 0)
        
        self.uki_check = Gtk.CheckButton(label="Generate UKI (Unified Kernel Image)")
        box.pack_start(self.uki_check, False, False, 5)
        
        return box
    
    def create_kernel_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label(label="Select kernel:", xalign=0)
        box.pack_start(label, False, False, 0)
        
        kernel_store = Gtk.ListStore(str)
        for kernel in ["linux", "linux-zen", "linux-lts", "linux-hardened", 
                      "linux-libre", "linux-cachyos-bore", "linux-bazzite-bin", 
                      "xanmod", "tkg"]:
            kernel_store.append([kernel])
        
        self.kernel_combo = Gtk.ComboBox.new_with_model(kernel_store)
        renderer_text = Gtk.CellRendererText()
        self.kernel_combo.pack_start(renderer_text, True)
        self.kernel_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.kernel_combo, False, False, 0)
        
        microcode_label = Gtk.Label(label="Microcode:", xalign=0)
        box.pack_start(microcode_label, False, False, 5)
        
        microcode_store = Gtk.ListStore(str)
        for ucode in ["auto", "intel-ucode", "amd-ucode", "none"]:
            microcode_store.append([ucode])
        
        self.microcode_combo = Gtk.ComboBox.new_with_model(microcode_store)
        renderer_text = Gtk.CellRendererText()
        self.microcode_combo.pack_start(renderer_text, True)
        self.microcode_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.microcode_combo, False, False, 0)
        
        return box
    
    def create_init_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label(label="Select init system:", xalign=0)
        box.pack_start(label, False, False, 0)
        
        init_store = Gtk.ListStore(str)
        for init in ["openrc", "runit", "dinit", "s6"]:
            init_store.append([init])
        
        self.init_combo = Gtk.ComboBox.new_with_model(init_store)
        renderer_text = Gtk.CellRendererText()
        self.init_combo.pack_start(renderer_text, True)
        self.init_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.init_combo, False, False, 0)
        
        return box
    
    def create_desktop_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label(label="Select desktop environment / window manager:", xalign=0)
        box.pack_start(label, False, False, 0)
        
        de_store = Gtk.ListStore(str)
        for de in ["kde", "sonicde", "xfce4", "lxqt", "lxde", "hyprland", "sway", 
                  "niri", "i3wm", "dwm", "vxwm", "icewm", "mango", "none"]:
            de_store.append([de])
        
        self.de_combo = Gtk.ComboBox.new_with_model(de_store)
        renderer_text = Gtk.CellRendererText()
        self.de_combo.pack_start(renderer_text, True)
        self.de_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.de_combo, False, False, 0)
        
        dm_label = Gtk.Label(label="Display manager:", xalign=0)
        box.pack_start(dm_label, False, False, 5)
        
        dm_store = Gtk.ListStore(str)
        for dm in ["none", "lightdm", "sddm", "soniclogin"]:
            dm_store.append([dm])
        
        self.dm_combo = Gtk.ComboBox.new_with_model(dm_store)
        renderer_text = Gtk.CellRendererText()
        self.dm_combo.pack_start(renderer_text, True)
        self.dm_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.dm_combo, False, False, 0)
        
        return box
    
    def create_network_audio_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        net_label = Gtk.Label(label="Network stack:", xalign=0)
        box.pack_start(net_label, False, False, 0)
        
        net_store = Gtk.ListStore(str)
        for net in ["networkmanager", "dhcpcd+iwd", "connman", "none"]:
            net_store.append([net])
        
        self.net_combo = Gtk.ComboBox.new_with_model(net_store)
        renderer_text = Gtk.CellRendererText()
        self.net_combo.pack_start(renderer_text, True)
        self.net_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.net_combo, False, False, 0)
        
        audio_label = Gtk.Label(label="Audio stack:", xalign=0)
        box.pack_start(audio_label, False, False, 10)
        
        audio_store = Gtk.ListStore(str)
        for audio in ["pipewire", "pulseaudio", "none"]:
            audio_store.append([audio])
        
        self.audio_combo = Gtk.ComboBox.new_with_model(audio_store)
        renderer_text = Gtk.CellRendererText()
        self.audio_combo.pack_start(renderer_text, True)
        self.audio_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.audio_combo, False, False, 0)
        
        return box
    
    def create_extras_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        shell_label = Gtk.Label(label="Select user shell:", xalign=0)
        box.pack_start(shell_label, False, False, 0)
        
        shell_store = Gtk.ListStore(str)
        for shell in ["bash", "zsh", "fish"]:
            shell_store.append([shell])
        
        self.shell_combo = Gtk.ComboBox.new_with_model(shell_store)
        renderer_text = Gtk.CellRendererText()
        self.shell_combo.pack_start(renderer_text, True)
        self.shell_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.shell_combo, False, False, 0)
        
        extras_label = Gtk.Label(label="Extra packages:", xalign=0)
        box.pack_start(extras_label, False, False, 10)
        
        notebook = Gtk.Notebook()
        
        categories = {
            "System Tools": ["git", "flatpak", "fastfetch", "firewalld", "bluez", "zram-tools", "usb_modeswitch"],
            "Editors": ["nano", "vim", "neovim", "micro", "helix"],
            "Browsers": ["firefox", "chromium", "qutebrowser"],
            "File Managers": ["ranger", "lf", "nnn", "thunar"],
            "Terminals": ["alacritty", "kitty", "foot"],
            "Shell & Prompt": ["fzf", "zoxide", "starship", "eza", "tmux"],
            "Monitoring": ["btop", "htop", "nvtop"],
            "Media": ["mpv", "feh"]
        }
        
        self.__extras_checkboxes = {}
        self.__extras_notebook = notebook
        
        for cat_name, pkgs in categories.items():
            page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            page_box.set_margin_start(10)
            page_box.set_margin_top(10)
            
            for pkg in pkgs:
                check = Gtk.CheckButton(label=pkg)
                page_box.pack_start(check, False, False, 0)
                self.__extras_checkboxes[pkg] = check
            
            select_all = Gtk.Button(label=f"Select All {cat_name}")
            select_all.connect("clicked", self.on_select_all, (cat_name, pkgs))
            page_box.pack_start(select_all, False, False, 5)
            
            notebook.append_page(page_box, Gtk.Label(label=cat_name))
        
        box.pack_start(notebook, True, True, 0)
        
        return box
    
    def on_select_all(self, widget, data):
        cat_name, pkgs = data
        for pkg in pkgs:
            if pkg in self.__extras_checkboxes:
                self.__extras_checkboxes[pkg].set_active(True)
    
    def create_users_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        hostname_label = Gtk.Label(label="Hostname:", xalign=0)
        box.pack_start(hostname_label, False, False, 0)
        self.hostname_entry = Gtk.Entry()
        self.hostname_entry.set_text("artix")
        box.pack_start(self.hostname_entry, False, False, 0)
        
        tz_label = Gtk.Label(label="Timezone:", xalign=0)
        box.pack_start(tz_label, False, False, 5)
        self.timezone_entry = Gtk.Entry()
        self.timezone_entry.set_text("Europe/Belgrade")
        box.pack_start(self.timezone_entry, False, False, 0)
        
        locale_label = Gtk.Label(label="Locale:", xalign=0)
        box.pack_start(locale_label, False, False, 5)
        self.locale_entry = Gtk.Entry()
        self.locale_entry.set_text("en_US.UTF-8")
        box.pack_start(self.locale_entry, False, False, 0)
        
        keymap_label = Gtk.Label(label="Keyboard layout:", xalign=0)
        box.pack_start(keymap_label, False, False, 5)
        self.keymap_entry = Gtk.Entry()
        self.keymap_entry.set_text("us")
        box.pack_start(self.keymap_entry, False, False, 0)
        
        username_label = Gtk.Label(label="Username:", xalign=0)
        box.pack_start(username_label, False, False, 5)
        self.username_entry = Gtk.Entry()
        self.username_entry.set_text("artix")
        box.pack_start(self.username_entry, False, False, 0)
        
        user_pass_label = Gtk.Label(label="User Password:", xalign=0)
        box.pack_start(user_pass_label, False, False, 5)
        self.user_pass_entry = Gtk.Entry()
        self.user_pass_entry.set_visibility(False)
        self.user_pass_entry.set_invisible_char("*")
        box.pack_start(self.user_pass_entry, False, False, 0)
        
        user_confirm_label = Gtk.Label(label="Confirm User Password:", xalign=0)
        box.pack_start(user_confirm_label, False, False, 5)
        self.user_confirm_entry = Gtk.Entry()
        self.user_confirm_entry.set_visibility(False)
        self.user_confirm_entry.set_invisible_char("*")
        box.pack_start(self.user_confirm_entry, False, False, 0)
        
        root_pass_label = Gtk.Label(label="Root Password:", xalign=0)
        box.pack_start(root_pass_label, False, False, 5)
        self.root_pass_entry = Gtk.Entry()
        self.root_pass_entry.set_visibility(False)
        self.root_pass_entry.set_invisible_char("*")
        box.pack_start(self.root_pass_entry, False, False, 0)
        
        root_confirm_label = Gtk.Label(label="Confirm Root Password:", xalign=0)
        box.pack_start(root_confirm_label, False, False, 5)
        self.root_confirm_entry = Gtk.Entry()
        self.root_confirm_entry.set_visibility(False)
        self.root_confirm_entry.set_invisible_char("*")
        box.pack_start(self.root_confirm_entry, False, False, 0)
        
        return box
    
    def create_privilege_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        priv_label = Gtk.Label(label="Privilege escalation:", xalign=0)
        box.pack_start(priv_label, False, False, 0)
        
        priv_store = Gtk.ListStore(str)
        for priv in ["sudo", "doas"]:
            priv_store.append([priv])
        
        self.priv_combo = Gtk.ComboBox.new_with_model(priv_store)
        renderer_text = Gtk.CellRendererText()
        self.priv_combo.pack_start(renderer_text, True)
        self.priv_combo.add_attribute(renderer_text, "text", 0)
        box.pack_start(self.priv_combo, False, False, 0)
        
        self.arch_repos_check = Gtk.CheckButton(label="Enable Arch Linux repositories")
        box.pack_start(self.arch_repos_check, False, False, 5)
        
        self.offline_check = Gtk.CheckButton(label="Enable offline installation mode (cached packages)")
        box.pack_start(self.offline_check, False, False, 5)
        
        self.poweruser_check = Gtk.CheckButton(label="Enable Power User Mode (source compilation)")
        box.pack_start(self.poweruser_check, False, False, 10)
        
        self.poweruser_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.poweruser_box.set_margin_start(20)
        
        coreutils_label = Gtk.Label(label="Coreutils:", xalign=0)
        self.poweruser_box.pack_start(coreutils_label, False, False, 0)
        
        coreutils_store = Gtk.ListStore(str)
        for cu in ["gnu", "busybox", "uutils", "artix", "custom"]:
            coreutils_store.append([cu])
        
        self.coreutils_combo = Gtk.ComboBox.new_with_model(coreutils_store)
        renderer_text = Gtk.CellRendererText()
        self.coreutils_combo.pack_start(renderer_text, True)
        self.coreutils_combo.add_attribute(renderer_text, "text", 0)
        self.poweruser_box.pack_start(self.coreutils_combo, False, False, 0)
        
        keep_binary_label = Gtk.Label(label="Keep binary kernel as fallback:", xalign=0)
        self.poweruser_box.pack_start(keep_binary_label, False, False, 5)
        
        self.keep_binary_check = Gtk.CheckButton(label="Yes, keep binary kernel")
        self.keep_binary_check.set_active(True)
        self.poweruser_box.pack_start(self.keep_binary_check, False, False, 0)
        
        packages_label = Gtk.Label(label="Packages to build from source:", xalign=0)
        self.poweruser_box.pack_start(packages_label, False, False, 5)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(150)
        
        packages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        packages = ["linux", "glibc", "busybox", "openssl", "zlib", "zstd", "mesa"]
        self.poweruser_packages = []
        for pkg in packages:
            check = Gtk.CheckButton(label=pkg)
            self.poweruser_packages.append(check)
            packages_box.pack_start(check, False, False, 0)
        
        scroll.add(packages_box)
        self.poweruser_box.pack_start(scroll, True, True, 0)
        
        box.pack_start(self.poweruser_box, False, False, 0)
        self.poweruser_box.set_no_show_all(True)
        self.poweruser_box.hide()
        
        self.poweruser_check.connect("toggled", self.on_poweruser_toggled)
        
        return box
    
    def on_poweruser_toggled(self, check):
        if check.get_active():
            self.poweruser_box.show_all()
        else:
            self.poweruser_box.hide()
    
    def create_summary_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Installation Summary</span>')
        box.pack_start(label, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(400)
        
        self.summary_text = Gtk.TextView()
        self.summary_text.set_editable(False)
        self.summary_text.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.summary_text)
        box.pack_start(scrolled, True, True, 0)
        
        self.stack.connect("notify::visible-child", self.on_page_changed)
        
        return box
    
    def on_page_changed(self, stack, param):
        if self.stack.get_visible_child() == self.pages[-1]:
            self.update_summary()
    
    def update_summary(self):
        self.collect_state()
        
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
        # Theme
        if hasattr(self, 'theme_combo'):
            iter = self.theme_combo.get_active_iter()
            if iter:
                theme = self.theme_combo.get_model()[iter][0]
                if theme == "Gentoo":
                    self.state['GUM_TITLE_COLOR'] = "212"
                    self.state['GUM_ACCENT_COLOR'] = "34"
                elif theme == "Artix":
                    self.state['GUM_TITLE_COLOR'] = "39"
                    self.state['GUM_ACCENT_COLOR'] = "117"
                elif theme == "Jet Black":
                    self.state['GUM_TITLE_COLOR'] = "245"
                    self.state['GUM_ACCENT_COLOR'] = "196"
                elif theme == "Mono":
                    self.state['GUM_TITLE_COLOR'] = "250"
                    self.state['GUM_ACCENT_COLOR'] = "255"
                elif theme == "Retro":
                    self.state['GUM_TITLE_COLOR'] = "3"
                    self.state['GUM_ACCENT_COLOR'] = "11"
        
        # Filesystem
        if hasattr(self, 'fs_combo'):
            iter = self.fs_combo.get_active_iter()
            if iter:
                self.state['FS_TYPE'] = self.fs_combo.get_model()[iter][0]
        
        # BTRFS layout
        if hasattr(self, 'btrfs_combo') and self.state.get('FS_TYPE') == "btrfs":
            iter = self.btrfs_combo.get_active_iter()
            if iter:
                self.state['BTRFS_LAYOUT'] = self.btrfs_combo.get_model()[iter][0]
        
        # Bootloader
        if hasattr(self, 'bl_combo'):
            iter = self.bl_combo.get_active_iter()
            if iter:
                self.state['BOOTLOADER'] = self.bl_combo.get_model()[iter][0]
        
        # UKI
        if hasattr(self, 'uki_check'):
            self.state['GENERATE_UKI'] = "yes" if self.uki_check.get_active() else "no"
        
        # Kernel
        if hasattr(self, 'kernel_combo'):
            iter = self.kernel_combo.get_active_iter()
            if iter:
                self.state['KERNEL_CHOICE'] = self.kernel_combo.get_model()[iter][0]
        
        # Microcode
        if hasattr(self, 'microcode_combo'):
            iter = self.microcode_combo.get_active_iter()
            if iter:
                self.state['MICROCODE_OVERRIDE'] = self.microcode_combo.get_model()[iter][0]
        
        # Init
        if hasattr(self, 'init_combo'):
            iter = self.init_combo.get_active_iter()
            if iter:
                self.state['INIT'] = self.init_combo.get_model()[iter][0]
        
        # Desktop
        if hasattr(self, 'de_combo'):
            iter = self.de_combo.get_active_iter()
            if iter:
                self.state['WM_DE'] = self.de_combo.get_model()[iter][0]
        
        # Display manager
        if hasattr(self, 'dm_combo'):
            iter = self.dm_combo.get_active_iter()
            if iter:
                self.state['DISPLAY_MANAGER'] = self.dm_combo.get_model()[iter][0]
        
        # Network
        if hasattr(self, 'net_combo'):
            iter = self.net_combo.get_active_iter()
            if iter:
                self.state['NETWORK_STACK'] = self.net_combo.get_model()[iter][0]
        
        # Audio
        if hasattr(self, 'audio_combo'):
            iter = self.audio_combo.get_active_iter()
            if iter:
                self.state['AUDIO_STACK'] = self.audio_combo.get_model()[iter][0]
        
        # Shell
        if hasattr(self, 'shell_combo'):
            iter = self.shell_combo.get_active_iter()
            if iter:
                self.state['USER_SHELL'] = self.shell_combo.get_model()[iter][0]
        
        # Extras (NO STATE CORRUPTION EDITION)
        extras = []
        if hasattr(self, '_CommonPages__extras_notebook') and self._CommonPages__extras_notebook is not None:
            notebook = self._CommonPages__extras_notebook
            for i in range(notebook.get_n_pages()):
                page_box = notebook.get_nth_page(i)
                for child in page_box.get_children():
                    if isinstance(child, Gtk.CheckButton):
                        if child.get_active():
                            extras.append(child.get_label())
        elif hasattr(self, '_CommonPages__extras_checkboxes'):
            cb_dict = self._CommonPages__extras_checkboxes
            if isinstance(cb_dict, dict):
                for pkg, cb in cb_dict.items():
                    if cb and hasattr(cb, 'get_active') and cb.get_active():
                        extras.append(pkg)
        self.state['EXTRAS'] = " ".join(extras)

        # Hostname
        if hasattr(self, 'hostname_entry'):
            self.state['HOSTNAME'] = self.hostname_entry.get_text()
        
        # Timezone
        if hasattr(self, 'timezone_entry'):
            self.state['TIMEZONE'] = self.timezone_entry.get_text()
        
        # Locale
        if hasattr(self, 'locale_entry'):
            self.state['LOCALE'] = self.locale_entry.get_text()
        
        # Keymap
        if hasattr(self, 'keymap_entry'):
            self.state['KEYMAP'] = self.keymap_entry.get_text()
        
        # Username
        if hasattr(self, 'username_entry'):
            self.state['USER_NAME'] = self.username_entry.get_text()
        
        # User password
        if hasattr(self, 'user_pass_entry'):
            self.state['USER_PASS'] = self.user_pass_entry.get_text()
        
        # Root password
        if hasattr(self, 'root_pass_entry'):
            self.state['ROOT_PASS'] = self.root_pass_entry.get_text()
        
        # Privilege escalation
        if hasattr(self, 'priv_combo'):
            iter = self.priv_combo.get_active_iter()
            if iter:
                self.state['PRIV_ESCALATION'] = self.priv_combo.get_model()[iter][0]
        
        # Arch repos
        if hasattr(self, 'arch_repos_check'):
            self.state['ENABLE_ARCH_REPOS'] = "yes" if self.arch_repos_check.get_active() else "no"
        
        # Offline mode
        if hasattr(self, 'offline_check'):
            self.state['ALLOW_OFFLINE'] = "yes" if self.offline_check.get_active() else "no"
        
        # Power User
        if hasattr(self, 'poweruser_check'):
            self.state['POWER_USER'] = "yes" if self.poweruser_check.get_active() else "no"
            if hasattr(self, 'coreutils_combo') and self.poweruser_check.get_active():
                iter = self.coreutils_combo.get_active_iter()
                if iter:
                    self.state['COREUTILS'] = self.coreutils_combo.get_model()[iter][0]
            if hasattr(self, 'keep_binary_check'):
                self.state['KEEP_BINARY_KERNEL'] = "yes" if self.keep_binary_check.get_active() else "no"
            if hasattr(self, 'poweruser_packages'):
                selected = [cb.get_label() for cb in self.poweruser_packages if cb.get_active()]
                self.state['POWERUSER_PACKAGES'] = " ".join(selected)

        self.state['GUI_MODE'] = "yes"