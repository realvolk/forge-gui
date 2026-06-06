#!/usr/bin/env python3
import subprocess
import os
import json
import urllib.request
from gi.repository import Gtk
from .automatic import AutomaticWindow

# Community recipe repository
RECIPES_REPO = "https://raw.githubusercontent.com/realvolk/ArtixForge-recipes/main"
LIST_URL = f"{RECIPES_REPO}/.LIST"
SECTION_CONFIG = "/etc/artix-poweruser/recipe-sections.conf"

class PowerUserWindow(AutomaticWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state)
        self.window.set_title("Power User Installation")
        self.recipe_sections = self.load_sections()
        self.recipes = []  # Will be filled with (name, section, desc)
        self.fetch_recipe_list()
        self.feature_flags_per_package = {}  # name -> list of flags

        # Insert Power User pages after disk page (index 2)
        # Pages: 0 Welcome, 1 Theme, 2 Disk, then new ones
        poweruser_pages = [
            ("Power User – Profile", self.create_profile_page()),
            ("Power User – Recipe Sections", self.create_sections_page()),
            ("Power User – Packages", self.create_packages_page()),
            ("Power User – Coreutils & Fallback", self.create_coreutils_page()),
            ("Power User – Kernel Config", self.create_kernel_config_page()),
            ("Power User – Kernel Hardware", self.create_kernel_hardware_page()),
            ("Power User – Feature Flags", self.create_feature_flags_page()),
            ("Power User – New Recipe", self.create_new_recipe_page()),
        ]
        insert_pos = 3
        for title, page in reversed(poweruser_pages):
            self.add_page(title, page)
            self.pages.insert(insert_pos, self.pages.pop())
        self.stack.set_visible_child(self.pages[0])

    def load_sections(self):
        sections = {"OFFICIAL/Base", "OFFICIAL/Other", "COMMUNITY/Base", "COMMUNITY/Other"}
        if os.path.exists(SECTION_CONFIG):
            with open(SECTION_CONFIG, 'r') as f:
                for line in f:
                    if line.startswith("GARTIX_SECTIONS="):
                        value = line.split('=')[1].strip().strip('"')
                        sections = set(value.split())
                        break
        return sections

    def save_sections(self):
        with open(SECTION_CONFIG, 'w') as f:
            f.write(f'GARTIX_SECTIONS="{" ".join(self.recipe_sections)}"\n')

    def fetch_recipe_list(self):
        try:
            with urllib.request.urlopen(LIST_URL) as resp:
                data = resp.read().decode('utf-8')
                self.recipes = []
                for line in data.strip().split('\n'):
                    if '|' in line:
                        name, section, desc = line.split('|', 2)
                        if section in self.recipe_sections:
                            self.recipes.append((name, section, desc))
        except Exception:
            self.recipes = [("linux", "OFFICIAL/Base", "Kernel")]  # fallback

    def create_profile_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Compilation Profile</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Choose optimization level for source builds.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 5)

        self.profile_combo = Gtk.ComboBoxText()
        for p in ["default", "safe", "performance", "hardened"]:
            self.profile_combo.append_text(p)
        self.profile_combo.set_active(0)
        box.pack_start(self.profile_combo, False, False, 5)

        self.tweak_btn = Gtk.Button(label="Tweak flags")
        self.tweak_btn.connect("clicked", self.on_tweak_flags)
        box.pack_start(self.tweak_btn, False, False, 5)

        self.profile_preview = Gtk.Label()
        self.profile_preview.set_justify(Gtk.Justification.LEFT)
        self.profile_preview.set_margin_top(10)
        box.pack_start(self.profile_preview, False, False, 0)

        self.profile_combo.connect("changed", self.on_profile_changed)
        self.on_profile_changed(self.profile_combo)
        return box

    def on_profile_changed(self, widget):
        profile = widget.get_active_text()
        flags = {
            "default":  ("-O2 -pipe", "-O2 -pipe", "", "-j$(nproc)"),
            "safe":     ("-O2 -pipe -fno-omit-frame-pointer", "-O2 -pipe -fno-omit-frame-pointer", "", "-j$(nproc)"),
            "performance": ("-O3 -march=native -pipe", "-O3 -march=native -pipe", "", "-j$(nproc)"),
            "hardened": ("-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-Wl,-z,relro,-z,now", "-j$(nproc)"),
        }
        cflags, cxxflags, ldflags, makeflags = flags.get(profile, flags["default"])
        self.profile_preview.set_text(f"CFLAGS: {cflags}\nCXXFLAGS: {cxxflags}\nLDFLAGS: {ldflags}\nMAKEFLAGS: {makeflags}")

    def on_tweak_flags(self, widget):
        dialog = Gtk.Dialog(title="Tweak Compilation Flags", parent=self.window, flags=Gtk.DialogFlags.MODAL)
        dialog.set_default_size(500, 300)
        vbox = dialog.get_content_area()
        vbox.set_spacing(10)

        def add_entry(label_text, default):
            lbl = Gtk.Label(label=label_text, xalign=0)
            vbox.pack_start(lbl, False, False, 0)
            entry = Gtk.Entry()
            entry.set_text(default)
            vbox.pack_start(entry, False, False, 0)
            return entry

        profile = self.profile_combo.get_active_text()
        flags = {
            "default": ("-O2 -pipe", "-O2 -pipe", "", "-j$(nproc)"),
            "safe": ("-O2 -pipe -fno-omit-frame-pointer", "-O2 -pipe -fno-omit-frame-pointer", "", "-j$(nproc)"),
            "performance": ("-O3 -march=native -pipe", "-O3 -march=native -pipe", "", "-j$(nproc)"),
            "hardened": ("-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-Wl,-z,relro,-z,now", "-j$(nproc)"),
        }
        cflags, cxxflags, ldflags, makeflags = flags.get(profile, flags["default"])
        cflags_entry = add_entry("CFLAGS", cflags)
        cxxflags_entry = add_entry("CXXFLAGS", cxxflags)
        ldflags_entry = add_entry("LDFLAGS", ldflags)
        makeflags_entry = add_entry("MAKEFLAGS (e.g. -j4)", makeflags)

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)
        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.custom_cflags = cflags_entry.get_text()
            self.custom_cxxflags = cxxflags_entry.get_text()
            self.custom_ldflags = ldflags_entry.get_text()
            self.custom_makeflags = makeflags_entry.get_text()
        dialog.destroy()

    def create_sections_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Recipe Sections</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Select which recipe sections to include.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 5)

        self.section_checkboxes = {}
        sections = ["OFFICIAL/Base", "OFFICIAL/Other", "COMMUNITY/Base", "COMMUNITY/Other"]
        for sec in sections:
            check = Gtk.CheckButton(label=sec)
            check.set_active(sec in self.recipe_sections)
            self.section_checkboxes[sec] = check
            box.pack_start(check, False, False, 0)

        return box

    def create_packages_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Packages to Build</span>')
        box.pack_start(label, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        self.packages_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.package_checkboxes = {}
        for name, section, desc in self.recipes:
            check = Gtk.CheckButton(label=f"{name} [{section}] – {desc}")
            self.packages_container.pack_start(check, False, False, 0)
            self.package_checkboxes[name] = check
        scroll.add(self.packages_container)
        box.pack_start(scroll, True, True, 0)

        info_btn = Gtk.Button(label="Warning about glibc")
        info_btn.connect("clicked", self.on_glibc_warning)
        box.pack_start(info_btn, False, False, 5)
        return box

    def on_glibc_warning(self, widget):
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            message_format="Building glibc from source is DANGEROUS.\n\nA miscompiled glibc will make your system unbootable.\nKeep the binary package as a fallback.\n\nProceed only if you understand the risks."
        )
        dialog.run()
        dialog.destroy()

    def create_coreutils_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Coreutils & Fallback</span>')
        box.pack_start(label, False, False, 0)

        coreutils_label = Gtk.Label(label="Coreutils implementation:", xalign=0)
        box.pack_start(coreutils_label, False, False, 5)
        self.coreutils_combo = Gtk.ComboBoxText()
        for opt in ["gnu", "busybox", "uutils", "artix", "custom", "none"]:
            self.coreutils_combo.append_text(opt)
        self.coreutils_combo.set_active(0)
        box.pack_start(self.coreutils_combo, False, False, 5)

        fallback_frame = Gtk.Frame(label="Fallback binary kernel")
        fallback_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        fallback_box.set_margin_start(10)
        self.fallback_check = Gtk.CheckButton(label="Keep binary kernel as fallback (recommended)")
        self.fallback_check.set_active(True)
        fallback_box.pack_start(self.fallback_check, False, False, 0)
        fallback_frame.add(fallback_box)
        box.pack_start(fallback_frame, False, False, 10)

        return box

    def create_kernel_config_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Kernel Configuration Depth</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("How much control do you want over kernel configuration?")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 5)

        self.depth_combo = Gtk.ComboBoxText()
        for depth in [
            "localmodconfig – compile only currently loaded modules (recommended)",
            "Auto-detection – hardware pre-filled, review & adjust",
            "Manual – blank checklist, pick everything yourself",
            "menuconfig – full ncurses kernel editor"
        ]:
            self.depth_combo.append_text(depth)
        self.depth_combo.set_active(0)
        box.pack_start(self.depth_combo, False, False, 5)
        return box

    def create_kernel_hardware_page(self):
        notebook = Gtk.Notebook()
        notebook.set_margin_top(10)

        # GPU page
        gpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        gpu_box.set_margin_start(10)
        gpu_label = Gtk.Label(label="GPU Drivers", xalign=0)
        gpu_label.set_markup('<b>GPU Drivers</b>')
        gpu_box.pack_start(gpu_label, False, False, 0)
        self.gpu_checkboxes = {}
        for g in ["intel", "amd", "nvidia", "virtio", "vesa", "simpledrm"]:
            cb = Gtk.CheckButton(label=g)
            gpu_box.pack_start(cb, False, False, 0)
            self.gpu_checkboxes[g] = cb
        notebook.append_page(gpu_box, Gtk.Label(label="GPU"))

        # Network page
        net_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        net_box.set_margin_start(10)
        net_label = Gtk.Label(label="Network Drivers", xalign=0)
        net_label.set_markup('<b>Network Drivers</b>')
        net_box.pack_start(net_label, False, False, 0)
        self.net_checkboxes = {}
        for n in ["intel", "realtek", "broadcom", "atheros", "virtio", "intel-wifi", "ath-wifi", "realtek-wifi", "bt"]:
            cb = Gtk.CheckButton(label=n)
            net_box.pack_start(cb, False, False, 0)
            self.net_checkboxes[n] = cb
        notebook.append_page(net_box, Gtk.Label(label="Network"))

        # Filesystems page
        fs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        fs_box.set_margin_start(10)
        fs_label = Gtk.Label(label="Filesystems", xalign=0)
        fs_label.set_markup('<b>Filesystems</b>')
        fs_box.pack_start(fs_label, False, False, 0)
        self.fs_checkboxes = {}
        for f in ["ext4", "btrfs", "xfs", "f2fs", "exfat", "ntfs", "overlay"]:
            cb = Gtk.CheckButton(label=f)
            fs_box.pack_start(cb, False, False, 0)
            self.fs_checkboxes[f] = cb
        notebook.append_page(fs_box, Gtk.Label(label="Filesystems"))

        # Sound page
        snd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        snd_box.set_margin_start(10)
        snd_label = Gtk.Label(label="Sound", xalign=0)
        snd_label.set_markup('<b>Sound</b>')
        snd_box.pack_start(snd_label, False, False, 0)
        self.snd_checkboxes = {}
        for s in ["intel-hda", "amd-hda", "usb-audio"]:
            cb = Gtk.CheckButton(label=s)
            snd_box.pack_start(cb, False, False, 0)
            self.snd_checkboxes[s] = cb
        notebook.append_page(snd_box, Gtk.Label(label="Sound"))

        # USB page
        usb_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        usb_box.set_margin_start(10)
        usb_label = Gtk.Label(label="USB", xalign=0)
        usb_label.set_markup('<b>USB</b>')
        usb_box.pack_start(usb_label, False, False, 0)
        self.usb_checkboxes = {}
        for u in ["storage", "hid", "serial"]:
            cb = Gtk.CheckButton(label=u)
            usb_box.pack_start(cb, False, False, 0)
            self.usb_checkboxes[u] = cb
        notebook.append_page(usb_box, Gtk.Label(label="USB"))

        # Security page
        sec_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sec_box.set_margin_start(10)
        sec_label = Gtk.Label(label="Security", xalign=0)
        sec_label.set_markup('<b>Security</b>')
        sec_box.pack_start(sec_label, False, False, 0)
        self.sec_checkboxes = {}
        for s in ["selinux", "apparmor", "lockdown"]:
            cb = Gtk.CheckButton(label=s)
            sec_box.pack_start(cb, False, False, 0)
            self.sec_checkboxes[s] = cb
        notebook.append_page(sec_box, Gtk.Label(label="Security"))

        # Virtualization page
        virt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        virt_box.set_margin_start(10)
        virt_label = Gtk.Label(label="Virtualization", xalign=0)
        virt_label.set_markup('<b>Virtualization</b>')
        virt_box.pack_start(virt_label, False, False, 0)
        self.virt_checkboxes = {}
        for v in ["kvm", "vhost"]:
            cb = Gtk.CheckButton(label=v)
            virt_box.pack_start(cb, False, False, 0)
            self.virt_checkboxes[v] = cb
        notebook.append_page(virt_box, Gtk.Label(label="Virtualization"))

        # Debugging page
        dbg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        dbg_box.set_margin_start(10)
        dbg_label = Gtk.Label(label="Debugging", xalign=0)
        dbg_label.set_markup('<b>Debugging & Tracing</b>')
        dbg_box.pack_start(dbg_label, False, False, 0)
        self.dbg_checkboxes = {}
        for d in ["ftrace", "perf", "kprobes", "ebpf"]:
            cb = Gtk.CheckButton(label=d)
            dbg_box.pack_start(cb, False, False, 0)
            self.dbg_checkboxes[d] = cb
        notebook.append_page(dbg_box, Gtk.Label(label="Debugging"))

        # Preemption, timer, governor (simple dropdowns)
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        bottom_box.set_margin_top(10)

        preempt_label = Gtk.Label(label="Preemption model:", xalign=0)
        bottom_box.pack_start(preempt_label, False, False, 0)
        self.preempt_combo = Gtk.ComboBoxText()
        for p in ["voluntary", "full", "rt"]:
            self.preempt_combo.append_text(p)
        self.preempt_combo.set_active(0)
        bottom_box.pack_start(self.preempt_combo, False, False, 0)

        timer_label = Gtk.Label(label="Timer frequency (Hz):", xalign=0)
        bottom_box.pack_start(timer_label, False, False, 0)
        self.timer_combo = Gtk.ComboBoxText()
        for t in ["100", "250", "300", "1000"]:
            self.timer_combo.append_text(t)
        self.timer_combo.set_active(1)  # 250
        bottom_box.pack_start(self.timer_combo, False, False, 0)

        gov_label = Gtk.Label(label="Default CPU governor:", xalign=0)
        bottom_box.pack_start(gov_label, False, False, 0)
        self.gov_combo = Gtk.ComboBoxText()
        for g in ["schedutil", "ondemand", "performance"]:
            self.gov_combo.append_text(g)
        self.gov_combo.set_active(0)
        bottom_box.pack_start(self.gov_combo, False, False, 0)

        # Combine notebook and bottom_box in a vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.pack_start(notebook, True, True, 0)
        main_box.pack_start(bottom_box, False, False, 0)
        return main_box

    def create_feature_flags_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Feature Flags</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Select optional features for each package that supports them.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 5)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        self.flags_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scroll.add(self.flags_container)
        box.pack_start(scroll, True, True, 0)

        # Fetch feature flags for all selected packages later (dynamic)
        return box

    def create_new_recipe_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Create New Recipe</span>')
        box.pack_start(label, False, False, 0)

        desc = Gtk.Label()
        desc.set_text("Create a custom recipe for a package not in the community repository.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 5)

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(10)

        row = 0
        grid.attach(Gtk.Label(label="Package name:", xalign=0), 0, row, 1, 1)
        self.new_name_entry = Gtk.Entry()
        grid.attach(self.new_name_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Version (e.g. 1.0):", xalign=0), 0, row, 1, 1)
        self.new_ver_entry = Gtk.Entry()
        grid.attach(self.new_ver_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Source URL:", xalign=0), 0, row, 1, 1)
        self.new_url_entry = Gtk.Entry()
        grid.attach(self.new_url_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Description:", xalign=0), 0, row, 1, 1)
        self.new_desc_entry = Gtk.Entry()
        grid.attach(self.new_desc_entry, 1, row, 1, 1)

        row += 1
        grid.attach(Gtk.Label(label="Dependencies (space-separated):", xalign=0), 0, row, 1, 1)
        self.new_deps_entry = Gtk.Entry()
        grid.attach(self.new_deps_entry, 1, row, 1, 1)

        box.pack_start(grid, False, False, 0)

        create_btn = Gtk.Button(label="Create Recipe")
        create_btn.connect("clicked", self.on_create_recipe)
        box.pack_start(create_btn, False, False, 10)

        return box

    def on_create_recipe(self, widget):
        name = self.new_name_entry.get_text().strip()
        if not name:
            self.show_message("Error", "Package name is required.")
            return
        version = self.new_ver_entry.get_text().strip() or "1.0"
        url = self.new_url_entry.get_text().strip()
        desc = self.new_desc_entry.get_text().strip() or "Custom recipe"
        deps = self.new_deps_entry.get_text().strip()

        # Create recipe file in POWERUSER_DIR/recipes/
        recipe_path = f"/usr/share/artix-poweruser/recipes/{name}.sh"
        try:
            with open(recipe_path, 'w') as f:
                f.write(f"""#!/usr/bin/env bash
pkgname={name}
pkgver={version}
pkgrel=1
desc="{desc}"
url="{url}"

sources=(
  "{url}|SKIP|{name}-${{pkgver}}.tar.gz"
)

depends=({deps})
makedepends=(base-devel)

prepare() {{
  cd "$BUILD_DIR"
  tar xf "$SOURCES_DIR/{name}-$pkgver.tar.gz"
  mv "{name}-$pkgver" src
}}

configure() {{
  cd "$BUILD_DIR/src"
  ./configure --prefix=/usr
}}

build() {{
  cd "$BUILD_DIR/src"
  make -j$ARTIX_MAKEFLAGS
}}

package() {{
  cd "$BUILD_DIR/src"
  make DESTDIR="$PKG_DESTDIR" install
}}
""")
            self.show_message("Success", f"Recipe {name}.sh created.")
        except Exception as e:
            self.show_message("Error", f"Failed to create recipe: {e}")

    def show_message(self, title, msg):
        dialog = Gtk.MessageDialog(parent=self.window, flags=Gtk.DialogFlags.MODAL,
                                   type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK,
                                   message_format=msg)
        dialog.set_title(title)
        dialog.run()
        dialog.destroy()

    def collect_state(self):
        # First collect from AutomaticWindow
        super().collect_state()

        # Profile
        if hasattr(self, 'profile_combo'):
            self.state['POWERUSER_PROFILE'] = self.profile_combo.get_active_text()
            if hasattr(self, 'custom_cflags'):
                self.state['ARTIX_CFLAGS'] = self.custom_cflags
                self.state['ARTIX_CXXFLAGS'] = self.custom_cxxflags
                self.state['ARTIX_LDFLAGS'] = self.custom_ldflags
                self.state['ARTIX_MAKEFLAGS'] = self.custom_makeflags

        # Recipe sections
        if hasattr(self, 'section_checkboxes'):
            sections = [sec for sec, cb in self.section_checkboxes.items() if cb.get_active()]
            self.recipe_sections = set(sections)
            self.save_sections()

        # Packages
        selected_packages = []
        if hasattr(self, 'package_checkboxes'):
            for name, cb in self.package_checkboxes.items():
                if cb.get_active():
                    selected_packages.append(name)
            self.state['POWERUSER_PACKAGES'] = " ".join(selected_packages)

        # Coreutils & fallback
        if hasattr(self, 'coreutils_combo'):
            self.state['COREUTILS'] = self.coreutils_combo.get_active_text()
        if hasattr(self, 'fallback_check'):
            self.state['KEEP_BINARY_KERNEL'] = "yes" if self.fallback_check.get_active() else "no"

        # Kernel config depth
        if hasattr(self, 'depth_combo'):
            depth_text = self.depth_combo.get_active_text()
            if depth_text.startswith("localmodconfig"):
                self.state['KERNEL_CONFIG_DEPTH'] = "localmodconfig"
            elif depth_text.startswith("Auto"):
                self.state['KERNEL_CONFIG_DEPTH'] = "auto"
            elif depth_text.startswith("Manual"):
                self.state['KERNEL_CONFIG_DEPTH'] = "manual"
            elif depth_text.startswith("menuconfig"):
                self.state['KERNEL_CONFIG_DEPTH'] = "menuconfig"

        # Hardware checklists
        if hasattr(self, 'gpu_checkboxes'):
            gpu = [g for g, cb in self.gpu_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_GPU'] = " ".join(gpu)
        if hasattr(self, 'net_checkboxes'):
            net = [n for n, cb in self.net_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_NET'] = " ".join(net)
        if hasattr(self, 'fs_checkboxes'):
            fs = [f for f, cb in self.fs_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_FS'] = " ".join(fs)
        if hasattr(self, 'snd_checkboxes'):
            snd = [s for s, cb in self.snd_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_SOUND'] = " ".join(snd)
        if hasattr(self, 'usb_checkboxes'):
            usb = [u for u, cb in self.usb_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_USB'] = " ".join(usb)
        if hasattr(self, 'sec_checkboxes'):
            sec = [s for s, cb in self.sec_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_SECURITY'] = " ".join(sec)
        if hasattr(self, 'virt_checkboxes'):
            virt = [v for v, cb in self.virt_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_VIRT'] = " ".join(virt)
        if hasattr(self, 'dbg_checkboxes'):
            dbg = [d for d, cb in self.dbg_checkboxes.items() if cb.get_active()]
            self.state['KERNEL_ADV_DEBUG'] = " ".join(dbg)

        # Preemption, timer, governor
        if hasattr(self, 'preempt_combo'):
            self.state['KERNEL_PREEMPT'] = self.preempt_combo.get_active_text()
        if hasattr(self, 'timer_combo'):
            self.state['KERNEL_TIMER'] = self.timer_combo.get_active_text()
        if hasattr(self, 'gov_combo'):
            self.state['KERNEL_GOVERNOR'] = self.gov_combo.get_active_text()

        # Feature flags (would need to be populated based on selected packages)
        # For simplicity, skipomg dynamic feature flags in this version, but the page exists.

        self.state['POWER_USER'] = "yes"