#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import os
import urllib.request
from gi.repository import Gtk, Gdk
from .automatic import AutomaticWindow

RECIPES_REPO = "https://raw.githubusercontent.com/realvolk/ArtixForge-recipes/main"
LIST_URL = f"{RECIPES_REPO}/.LIST"
SECTION_CONFIG = "/etc/artix-poweruser/recipe-sections.conf"

class PowerUserWindow(AutomaticWindow):
    def __init__(self, state_file, state):
        self._kernel_hardware_page_idx = None
        self._new_recipe_page_idx = None
        self._coreutils_page_idx = None
        self._kernel_config_page_idx = None
        self._feature_flags_page_idx = None

        super().__init__(state_file, state)
        self.window.set_title("Power User Installation")
        self.recipe_sections = self.load_sections()
        self.recipes = []
        self.fetch_recipe_list()
        self.feature_flags_per_package = {}

        poweruser_page_specs = [
            ("Power User – Profile", self.create_profile_page),
            ("Power User – Recipe Sections", self.create_sections_page),
            ("Power User – Packages", self.create_packages_page),
            ("Power User – Coreutils & Fallback", self.create_coreutils_page),
            ("Power User – Kernel Config", self.create_kernel_config_page),
            ("Power User – Kernel Hardware", self.create_kernel_hardware_page),
            ("Power User – Feature Flags", self.create_feature_flags_page),
            ("Power User – New Recipe", self.create_new_recipe_page),
        ]

        insert_pos = 3
        for i, (title, factory) in enumerate(poweruser_page_specs):
            page = factory()
            self.add_page(title, page)
            self.pages.insert(insert_pos + i, self.pages.pop())

        for i, page in enumerate(self.pages):
            title = self.stack.get_page(page).get_name()
            if title == "Power User – Kernel Hardware":
                self._kernel_hardware_page_idx = i
            elif title == "Power User – New Recipe":
                self._new_recipe_page_idx = i
            elif title == "Power User – Coreutils & Fallback":
                self._coreutils_page_idx = i
            elif title == "Power User – Kernel Config":
                self._kernel_config_page_idx = i
            elif title == "Power User – Feature Flags":
                self._feature_flags_page_idx = i

        if hasattr(self, 'coreutils_combo'):
            self.coreutils_combo.connect("notify::selected", self._on_coreutils_changed)

        self.stack.set_visible_child(self.pages[0])

    def _set_page_visible(self, page_idx, visible):
        if page_idx is None or page_idx >= len(self.pages):
            return
        page = self.pages[page_idx]
        page.set_visible(visible)

    def _on_package_toggled(self, check, pkg_name):
        if pkg_name == "linux":
            self._update_conditional_pages()

    def _on_coreutils_changed(self, combo, param):
        self._update_conditional_pages()

    def _update_conditional_pages(self):
        linux_selected = False
        if hasattr(self, 'package_checkboxes') and "linux" in self.package_checkboxes:
            linux_selected = self.package_checkboxes["linux"].get_active()
        self._set_page_visible(self._kernel_hardware_page_idx, linux_selected)
        self._set_page_visible(self._kernel_config_page_idx, linux_selected)
        self._set_page_visible(self._feature_flags_page_idx, linux_selected)
        if hasattr(self, 'fallback_check'):
            self.fallback_check.set_sensitive(linux_selected)

        custom_selected = False
        if hasattr(self, 'coreutils_combo'):
            cu_values = ["gnu", "busybox", "uutils", "artix", "custom", "none"]
            idx = self.coreutils_combo.get_selected()
            if 0 <= idx < len(cu_values):
                custom_selected = (cu_values[idx] == "custom")
        self._set_page_visible(self._new_recipe_page_idx, custom_selected)
        self.update_nav_buttons()

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
        os.makedirs(os.path.dirname(SECTION_CONFIG), exist_ok=True)
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
            self.recipes = [("linux", "OFFICIAL/Base", "Kernel")]

    def create_profile_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Compilation Profile</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Choose optimization level for source builds.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.profile_combo = Gtk.DropDown.new(Gtk.StringList.new(["default", "safe", "performance", "hardened"]))
        box.append(self.profile_combo)
        self.tweak_btn = Gtk.Button(label="Tweak flags")
        self.tweak_btn.connect("clicked", self.on_tweak_flags)
        box.append(self.tweak_btn)
        self.profile_preview = Gtk.Label()
        self.profile_preview.set_justify(Gtk.Justification.LEFT)
        self.profile_preview.set_margin_top(10)
        box.append(self.profile_preview)
        self.profile_combo.connect("notify::selected", self.on_profile_changed)
        self.on_profile_changed(self.profile_combo, None)
        return box

    def on_profile_changed(self, widget, param):
        values = ["default", "safe", "performance", "hardened"]
        idx = widget.get_selected()
        profile = values[idx] if 0 <= idx < len(values) else "default"
        flags = {
            "default":  ("-O2 -pipe", "-O2 -pipe", "", "-j$(nproc)"),
            "safe":     ("-O2 -pipe -fno-omit-frame-pointer", "-O2 -pipe -fno-omit-frame-pointer", "", "-j$(nproc)"),
            "performance": ("-O3 -march=native -pipe", "-O3 -march=native -pipe", "", "-j$(nproc)"),
            "hardened": ("-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-Wl,-z,relro,-z,now", "-j$(nproc)"),
        }
        cflags, cxxflags, ldflags, makeflags = flags.get(profile, flags["default"])
        self.profile_preview.set_text(f"CFLAGS: {cflags}\nCXXFLAGS: {cxxflags}\nLDFLAGS: {ldflags}\nMAKEFLAGS: {makeflags}")

    def on_tweak_flags(self, widget):
        dialog = Gtk.Dialog(title="Tweak Compilation Flags", transient_for=self.window, modal=True)
        dialog.set_default_size(500, 300)
        vbox = dialog.get_content_area()
        vbox.set_spacing(10)

        def add_entry(label_text, default):
            lbl = Gtk.Label(label=label_text, xalign=0)
            vbox.append(lbl)
            entry = Gtk.Entry()
            entry.set_text(default)
            vbox.append(entry)
            return entry

        values = ["default", "safe", "performance", "hardened"]
        idx = self.profile_combo.get_selected()
        profile = values[idx] if 0 <= idx < len(values) else "default"
        flags_map = {
            "default": ("-O2 -pipe", "-O2 -pipe", "", "-j$(nproc)"),
            "safe": ("-O2 -pipe -fno-omit-frame-pointer", "-O2 -pipe -fno-omit-frame-pointer", "", "-j$(nproc)"),
            "performance": ("-O3 -march=native -pipe", "-O3 -march=native -pipe", "", "-j$(nproc)"),
            "hardened": ("-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-Wl,-z,relro,-z,now", "-j$(nproc)"),
        }
        cflags, cxxflags, ldflags, makeflags = flags_map.get(profile, flags_map["default"])
        cflags_entry = add_entry("CFLAGS", cflags)
        cxxflags_entry = add_entry("CXXFLAGS", cxxflags)
        ldflags_entry = add_entry("LDFLAGS", ldflags)
        makeflags_entry = add_entry("MAKEFLAGS (e.g. -j4)", makeflags)

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)
        dialog.show()
        dialog.connect("response", self._on_tweak_response, cflags_entry, cxxflags_entry, ldflags_entry, makeflags_entry)

    def _on_tweak_response(self, dialog, response, cflags_entry, cxxflags_entry, ldflags_entry, makeflags_entry):
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
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Select which recipe sections to include.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.section_checkboxes = {}
        sections = ["OFFICIAL/Base", "OFFICIAL/Other", "COMMUNITY/Base", "COMMUNITY/Other"]
        for sec in sections:
            check = Gtk.CheckButton(label=sec)
            check.set_active(sec in self.recipe_sections)
            self.section_checkboxes[sec] = check
            box.append(check)
        return box

    def create_packages_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Packages to Build</span>')
        box.append(label)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        self.packages_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.package_checkboxes = {}
        for name, section, desc in self.recipes:
            check = Gtk.CheckButton(label=f"{name} [{section}] – {desc}")
            self.packages_container.append(check)
            self.package_checkboxes[name] = check
            check.connect("toggled", self._on_package_toggled, name)
        scroll.set_child(self.packages_container)
        box.append(scroll)
        info_btn = Gtk.Button(label="Warning about glibc")
        info_btn.connect("clicked", self.on_glibc_warning)
        box.append(info_btn)
        return box

    def on_glibc_warning(self, widget):
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
                                   message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                                   text="Building glibc from source is DANGEROUS.\n\nA miscompiled glibc will make your system unbootable.\nKeep the binary package as a fallback.\n\nProceed only if you understand the risks.")
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())

    def create_coreutils_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Coreutils &amp; Fallback</span>')
        box.append(label)
        coreutils_label = Gtk.Label(label="Coreutils implementation:", xalign=0)
        box.append(coreutils_label)
        self.coreutils_combo = Gtk.DropDown.new(Gtk.StringList.new(["gnu", "busybox", "uutils", "artix", "custom", "none"]))
        box.append(self.coreutils_combo)
        fallback_frame = Gtk.Frame(label="Fallback binary kernel")
        fallback_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        fallback_box.set_margin_start(10)
        self.fallback_check = Gtk.CheckButton(label="Keep binary kernel as fallback (recommended)")
        self.fallback_check.set_active(True)
        fallback_box.append(self.fallback_check)
        fallback_frame.set_child(fallback_box)
        box.append(fallback_frame)
        return box

    def create_kernel_config_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Kernel Configuration Depth</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("How much control do you want over kernel configuration?")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        self.depth_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "localmodconfig – compile only currently loaded modules (recommended)",
            "Auto-detection – hardware pre-filled, review & adjust",
            "Manual – blank checklist, pick everything yourself",
            "menuconfig – full ncurses kernel editor"
        ]))
        box.append(self.depth_combo)
        return box

    def create_kernel_hardware_page(self):
        notebook = Gtk.Notebook()
        notebook.set_margin_top(10)
        self._add_hw_tab(notebook, "GPU", ["intel", "amd", "nvidia", "virtio", "vesa", "simpledrm"], 'gpu_checkboxes')
        self._add_hw_tab(notebook, "Network", ["intel", "realtek", "broadcom", "atheros", "virtio", "intel-wifi", "ath-wifi", "realtek-wifi", "bt"], 'net_checkboxes')
        self._add_hw_tab(notebook, "Filesystems", ["ext4", "btrfs", "xfs", "f2fs", "exfat", "ntfs", "overlay"], 'fs_checkboxes')
        self._add_hw_tab(notebook, "Sound", ["intel-hda", "amd-hda", "usb-audio"], 'snd_checkboxes')
        self._add_hw_tab(notebook, "USB", ["storage", "hid", "serial"], 'usb_checkboxes')
        self._add_hw_tab(notebook, "Security", ["selinux", "apparmor", "lockdown"], 'sec_checkboxes')
        self._add_hw_tab(notebook, "Virtualization", ["kvm", "vhost"], 'virt_checkboxes')
        self._add_hw_tab(notebook, "Debugging", ["ftrace", "perf", "kprobes", "ebpf"], 'dbg_checkboxes')

        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        bottom_box.set_margin_top(10)
        preempt_label = Gtk.Label(label="Preemption model:", xalign=0)
        bottom_box.append(preempt_label)
        self.preempt_combo = Gtk.DropDown.new(Gtk.StringList.new(["voluntary", "full", "rt"]))
        bottom_box.append(self.preempt_combo)
        timer_label = Gtk.Label(label="Timer frequency (Hz):", xalign=0)
        bottom_box.append(timer_label)
        self.timer_combo = Gtk.DropDown.new(Gtk.StringList.new(["100", "250", "300", "1000"]))
        self.timer_combo.set_selected(1)
        bottom_box.append(self.timer_combo)
        gov_label = Gtk.Label(label="Default CPU governor:", xalign=0)
        bottom_box.append(gov_label)
        self.gov_combo = Gtk.DropDown.new(Gtk.StringList.new(["schedutil", "ondemand", "performance"]))
        bottom_box.append(self.gov_combo)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.append(notebook)
        main_box.append(bottom_box)
        return main_box

    def _add_hw_tab(self, notebook, title, items, attr):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_margin_start(10)
        lbl = Gtk.Label(label=f"{title}", xalign=0)
        lbl.set_markup(f'<b>{title}</b>')
        box.append(lbl)
        checks = {}
        for item in items:
            cb = Gtk.CheckButton(label=item)
            box.append(cb)
            checks[item] = cb
        setattr(self, attr, checks)
        notebook.append_page(box, Gtk.Label(label=title))

    def create_feature_flags_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Feature Flags</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Select optional features for each package that supports them.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        self.flags_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scroll.set_child(self.flags_container)
        box.append(scroll)
        return box

    def create_new_recipe_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Create New Recipe</span>')
        box.append(label)
        desc = Gtk.Label()
        desc.set_text("Create a custom recipe for a package not in the community repository.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)
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
        box.append(grid)
        create_btn = Gtk.Button(label="Create Recipe")
        create_btn.connect("clicked", self.on_create_recipe)
        box.append(create_btn)
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
        dialog = Gtk.MessageDialog(transient_for=self.window, modal=True,
                                   message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=msg)
        dialog.set_title(title)
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())

    def _get_combo(self, combo, values):
        idx = combo.get_selected()
        return values[idx] if 0 <= idx < len(values) else values[0]

    def collect_state(self):
        if not self.collect_state_common():
            return

        if hasattr(self, 'disk_combo'):
            model = self.disk_combo.get_model()
            idx = self.disk_combo.get_selected()
            if model and 0 <= idx < model.get_n_items():
                self.state['DISK'] = model.get_string(idx)
        if hasattr(self, 'swap_check'):
            self.state['SWAP_ENABLED'] = "yes" if self.swap_check.get_active() else "no"
        if hasattr(self, 'luks_check'):
            self.state['USE_LUKS'] = "yes" if self.luks_check.get_active() else "no"
            if hasattr(self, 'luks_pass_entry') and self.luks_check.get_active():
                self.state['LUKS_PASS'] = self.luks_pass_entry.get_text()
        if hasattr(self, 'lvm_check'):
            self.state['USE_LVM'] = "yes" if self.lvm_check.get_active() else "no"

        self.state['MODE'] = 'power'
        self.state['POWER_USER'] = "yes"
        self.state['GUI_MODE'] = "yes"

        if hasattr(self, 'profile_combo'):
            self.state['POWERUSER_PROFILE'] = self._get_combo(self.profile_combo, ["default", "safe", "performance", "hardened"])
            if hasattr(self, 'custom_cflags'):
                self.state['ARTIX_CFLAGS'] = self.custom_cflags
                self.state['ARTIX_CXXFLAGS'] = self.custom_cxxflags
                self.state['ARTIX_LDFLAGS'] = self.custom_ldflags
                self.state['ARTIX_MAKEFLAGS'] = self.custom_makeflags

        if hasattr(self, 'section_checkboxes'):
            sections = [sec for sec, cb in self.section_checkboxes.items() if cb.get_active()]
            self.recipe_sections = set(sections)
            self.save_sections()

        selected_packages = []
        if hasattr(self, 'package_checkboxes'):
            for name, cb in self.package_checkboxes.items():
                if cb.get_active():
                    selected_packages.append(name)
            self.state['POWERUSER_PACKAGES'] = " ".join(selected_packages)

        if hasattr(self, 'coreutils_combo'):
            self.state['COREUTILS'] = self._get_combo(self.coreutils_combo, ["gnu", "busybox", "uutils", "artix", "custom", "none"])
        if hasattr(self, 'fallback_check'):
            self.state['KEEP_BINARY_KERNEL'] = "yes" if self.fallback_check.get_active() else "no"

        if hasattr(self, 'depth_combo'):
            depth_values = ["localmodconfig", "auto", "manual", "menuconfig"]
            self.state['KERNEL_CONFIG_DEPTH'] = self._get_combo(self.depth_combo, depth_values)

        for attr, key in [('gpu_checkboxes', 'KERNEL_ADV_GPU'), ('net_checkboxes', 'KERNEL_ADV_NET'),
                          ('fs_checkboxes', 'KERNEL_ADV_FS'), ('snd_checkboxes', 'KERNEL_ADV_SOUND'),
                          ('usb_checkboxes', 'KERNEL_ADV_USB'), ('sec_checkboxes', 'KERNEL_ADV_SECURITY'),
                          ('virt_checkboxes', 'KERNEL_ADV_VIRT'), ('dbg_checkboxes', 'KERNEL_ADV_DEBUG')]:
            if hasattr(self, attr):
                checks = getattr(self, attr)
                selected = [k for k, cb in checks.items() if cb.get_active()]
                self.state[key] = " ".join(selected)

        if hasattr(self, 'preempt_combo'):
            self.state['KERNEL_PREEMPT'] = self._get_combo(self.preempt_combo, ["voluntary", "full", "rt"])
        if hasattr(self, 'timer_combo'):
            self.state['KERNEL_TIMER'] = self._get_combo(self.timer_combo, ["100", "250", "300", "1000"])
        if hasattr(self, 'gov_combo'):
            self.state['KERNEL_GOVERNOR'] = self._get_combo(self.gov_combo, ["schedutil", "ondemand", "performance"])

        self.state['POWER_USER'] = "yes"

    def start_installation(self):
        self.collect_state()
        if not self._validate_passwords():
            return
        self.save_state()
        self.run_installer()