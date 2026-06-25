#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import os
import urllib.request
from gi.repository import Gtk, Adw
from .base import InstallerApp

RECIPES_REPO = "https://raw.githubusercontent.com/realvolk/ArtixForge-recipes/main"
LIST_URL = f"{RECIPES_REPO}/.LIST"
SECTION_CONFIG = "/etc/artix-poweruser/recipe-sections.conf"
LOCAL_RECIPES_DIR = "/usr/share/artix-poweruser/recipes"


class PowerUserWizard:
    def __init__(self, app: InstallerApp):
        self.app = app
        self.recipe_sections = {"OFFICIAL/Base", "OFFICIAL/Other", "COMMUNITY/Base", "COMMUNITY/Other"}
        self.all_recipes = []
        self.recipes = []
        self.fetch_all_recipe_list()
        self.apply_section_filter()
        self.ensure_recipes_downloaded()
        self.feature_flags_per_package = {}

    def push_pages(self):
        nav = self.app.nav_view
        nav.push(Adw.NavigationPage(child=self.app.create_welcome_page(), title="Welcome"))
        nav.push(Adw.NavigationPage(child=self.app.create_theme_page(), title="Theme"))
        nav.push(Adw.NavigationPage(child=self._create_disk_page(), title="Disk & Partitioning"))
        nav.push(Adw.NavigationPage(child=self.app.create_filesystem_page(), title="Filesystem"))
        nav.push(Adw.NavigationPage(child=self.app.create_bootloader_page(), title="Bootloader"))
        nav.push(Adw.NavigationPage(child=self.app.create_kernel_page(), title="Kernel"))
        nav.push(Adw.NavigationPage(child=self.app.create_init_page(), title="Init System"))
        nav.push(Adw.NavigationPage(child=self.app.create_desktop_page(), title="Desktop"))
        nav.push(Adw.NavigationPage(child=self.app.create_network_audio_page(), title="Network & Audio"))
        nav.push(Adw.NavigationPage(child=self.app.create_extras_page(), title="Shell & Extras"))
        nav.push(Adw.NavigationPage(child=self.app.create_users_page(), title="Users"))
        nav.push(Adw.NavigationPage(child=self._create_profile_page(), title="Power User – Profile"))
        nav.push(Adw.NavigationPage(child=self._create_sections_page(), title="Recipe Sections"))
        nav.push(Adw.NavigationPage(child=self._create_packages_page(), title="Packages"))
        nav.push(Adw.NavigationPage(child=self._create_coreutils_page(), title="Coreutils & Fallback"))
        nav.push(Adw.NavigationPage(child=self._create_kernel_config_page(), title="Kernel Config"))
        nav.push(Adw.NavigationPage(child=self._create_kernel_hardware_page(), title="Kernel Hardware"))
        nav.push(Adw.NavigationPage(child=self._create_feature_flags_page(), title="Feature Flags"))
        nav.push(Adw.NavigationPage(child=self._create_new_recipe_page(), title="New Recipe"))
        summary_page = self.app.create_summary_page(install_callback=self._on_install)
        self._update_summary()
        nav.push(Adw.NavigationPage(child=summary_page, title="Summary"))


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

    def fetch_all_recipe_list(self):
        try:
            with urllib.request.urlopen(LIST_URL) as resp:
                data = resp.read().decode('utf-8')
                self.all_recipes = []
                for line in data.strip().split('\n'):
                    if '|' in line:
                        parts = line.split('|', 2)
                        if len(parts) >= 3:
                            name, section, desc = parts
                            self.all_recipes.append((name, section, desc))
        except Exception:
            self.all_recipes = [("linux", "OFFICIAL/Base", "Kernel")]

    def apply_section_filter(self):
        self.recipes = [(n, s, d) for n, s, d in self.all_recipes if s in self.recipe_sections]

    def ensure_recipes_downloaded(self):
        os.makedirs(LOCAL_RECIPES_DIR, exist_ok=True)
        for name, section, desc in self.recipes:
            path = os.path.join(LOCAL_RECIPES_DIR, f"{name}.sh")
            if name == "template" or os.path.exists(path):
                continue
            url = f"{RECIPES_REPO}/{section}/{name}.sh"
            try:
                urllib.request.urlretrieve(url, path)
            except Exception:
                pass

    def _rebuild_packages_page(self):
        if not hasattr(self, 'packages_container'):
            return
        while True:
            child = self.packages_container.get_first_child()
            if child is None:
                break
            self.packages_container.remove(child)
        self.app.package_checkboxes = {}
        for name, section, desc in self.recipes:
            label_text = f"{name} [{section}] – {desc}"
            check = Gtk.CheckButton(label=label_text)
            self.packages_container.append(check)
            self.app.package_checkboxes[name] = check


    def _create_disk_page(self):
        from .automatic import AutomaticWizard
        dummy = AutomaticWizard(self.app)
        return dummy._create_disk_page()


    def _create_profile_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Compilation Profile")

        self.app.profile_combo = Gtk.DropDown.new(Gtk.StringList.new(["default", "safe", "performance", "hardened"]))
        row = Adw.ActionRow(title="Profile", subtitle="Choose optimization level for source builds")
        row.add_suffix(self.app.profile_combo)
        group.add(row)

        self.app.tweak_btn = Gtk.Button(label="Tweak flags")
        self.app.tweak_btn.connect("clicked", self._on_tweak_flags)
        group.add(self.app.tweak_btn)

        self.app.profile_preview = Gtk.Label()
        self.app.profile_preview.set_justify(Gtk.Justification.LEFT)
        self.app.profile_preview.set_margin_top(10)
        group.add(self.app.profile_preview)

        def on_profile_changed(dropdown, _param):
            values = ["default", "safe", "performance", "hardened"]
            idx = dropdown.get_selected()
            profile = values[idx] if 0 <= idx < len(values) else "default"
            flags = {
                "default":  ("-O2 -pipe", "-O2 -pipe", "", "-j$(nproc)"),
                "safe":     ("-O2 -pipe -fno-omit-frame-pointer", "-O2 -pipe -fno-omit-frame-pointer", "", "-j$(nproc)"),
                "performance": ("-O3 -march=native -pipe", "-O3 -march=native -pipe", "", "-j$(nproc)"),
                "hardened": ("-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-O2 -pipe -fstack-protector-strong -D_FORTIFY_SOURCE=2", "-Wl,-z,relro,-z,now", "-j$(nproc)"),
            }
            cflags, cxxflags, ldflags, makeflags = flags.get(profile, flags["default"])
            self.app.profile_preview.set_text(f"CFLAGS: {cflags}\nCXXFLAGS: {cxxflags}\nLDFLAGS: {ldflags}\nMAKEFLAGS: {makeflags}")

        self.app.profile_combo.connect("notify::selected", on_profile_changed)
        on_profile_changed(self.app.profile_combo, None)

        page.add(group)
        return page

    def _on_tweak_flags(self, widget):
        dialog = Gtk.Dialog(title="Tweak Compilation Flags", transient_for=self.app.window, modal=True)
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
        idx = self.app.profile_combo.get_selected()
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
            self.app.custom_cflags = cflags_entry.get_text()
            self.app.custom_cxxflags = cxxflags_entry.get_text()
            self.app.custom_ldflags = ldflags_entry.get_text()
            self.app.custom_makeflags = makeflags_entry.get_text()
        dialog.destroy()

    def _create_sections_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Recipe Sections")
        desc = Gtk.Label()
        desc.set_text("Select which recipe sections to include. Recipes are fetched from the community repository and downloaded automatically.")
        desc.set_wrap(True)
        group.add(desc)

        self.section_checkboxes = {}
        sections = ["OFFICIAL/Base", "OFFICIAL/Other", "COMMUNITY/Base", "COMMUNITY/Other"]
        for sec in sections:
            check = Gtk.CheckButton(label=sec)
            check.set_active(sec in self.recipe_sections)
            check.connect("toggled", self._on_section_toggled, sec)
            self.section_checkboxes[sec] = check
            group.add(check)

        page.add(group)
        return page

    def _on_section_toggled(self, check, section):
        sections = {sec for sec, cb in self.section_checkboxes.items() if cb.get_active()}
        self.recipe_sections = sections
        self.save_sections()
        self.apply_section_filter()
        self.ensure_recipes_downloaded()
        self._rebuild_packages_page()

    def _create_packages_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Packages to Build")

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        self.packages_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.app.package_checkboxes = {}
        for name, section, desc in self.recipes:
            check = Gtk.CheckButton(label=f"{name} [{section}] – {desc}")
            self.packages_container.append(check)
            self.app.package_checkboxes[name] = check
        scroll.set_child(self.packages_container)
        group.add(scroll)

        info_btn = Gtk.Button(label="Warning about glibc")
        info_btn.connect("clicked", self._on_glibc_warning)
        group.add(info_btn)

        page.add(group)
        return page

    def _on_glibc_warning(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self.app.window, modal=True,
            message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
            text="Building glibc from source is DANGEROUS.\n\nA miscompiled glibc will make your system unbootable.\nKeep the binary package as a fallback.\n\nProceed only if you understand the risks."
        )
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())

    def _create_coreutils_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Coreutils & Fallback")

        self.app.coreutils_combo = Gtk.DropDown.new(Gtk.StringList.new(["gnu", "busybox", "uutils", "artix", "custom", "none"]))
        core_row = Adw.ActionRow(title="Coreutils implementation")
        core_row.add_suffix(self.app.coreutils_combo)
        group.add(core_row)

        self.app.keep_binary_switch = Gtk.Switch()
        self.app.keep_binary_switch.set_active(True)
        keep_row = Adw.ActionRow(title="Keep binary kernel as fallback", subtitle="Recommended")
        keep_row.add_suffix(self.app.keep_binary_switch)
        group.add(keep_row)

        page.add(group)
        return page

    def _create_kernel_config_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Kernel Configuration Depth")

        self.app.depth_combo = Gtk.DropDown.new(Gtk.StringList.new([
            "localmodconfig – compile only currently loaded modules (recommended)",
            "Auto-detection – hardware pre-filled, review & adjust",
            "Manual – blank checklist, pick everything yourself",
            "menuconfig – full ncurses kernel editor"
        ]))
        row = Adw.ActionRow(title="Configuration Depth", subtitle="How much control do you want over kernel configuration?")
        row.add_suffix(self.app.depth_combo)
        group.add(row)

        page.add(group)
        return page

    def _create_kernel_hardware_page(self):
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

        self.app.preempt_combo = Gtk.DropDown.new(Gtk.StringList.new(["voluntary", "full", "rt"]))
        preempt_row = Adw.ActionRow(title="Preemption model")
        preempt_row.add_suffix(self.app.preempt_combo)
        bottom_box.append(preempt_row)

        self.app.timer_combo = Gtk.DropDown.new(Gtk.StringList.new(["100", "250", "300", "1000"]))
        self.app.timer_combo.set_selected(1)
        timer_row = Adw.ActionRow(title="Timer frequency (Hz)")
        timer_row.add_suffix(self.app.timer_combo)
        bottom_box.append(timer_row)

        self.app.gov_combo = Gtk.DropDown.new(Gtk.StringList.new(["schedutil", "ondemand", "performance"]))
        gov_row = Adw.ActionRow(title="Default CPU governor")
        gov_row.add_suffix(self.app.gov_combo)
        bottom_box.append(gov_row)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.append(notebook)
        main_box.append(bottom_box)

        return main_box

    def _add_hw_tab(self, notebook, title, items, attr):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_margin_start(10)
        lbl = Gtk.Label()
        lbl.set_markup(f'<b>{title}</b>')
        box.append(lbl)
        checks = {}
        for item in items:
            cb = Gtk.CheckButton(label=item)
            box.append(cb)
            checks[item] = cb
        setattr(self.app, attr, checks)
        notebook.append_page(box, Gtk.Label(label=title))

    def _create_feature_flags_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Feature Flags")
        desc = Gtk.Label()
        desc.set_text("Select optional features for each package that supports them.")
        desc.set_wrap(True)
        group.add(desc)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(300)
        self.flags_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scroll.set_child(self.flags_container)
        group.add(scroll)

        page.add(group)
        return page

    def _create_new_recipe_page(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Create New Recipe")
        desc = Gtk.Label()
        desc.set_text("Create a custom recipe for a package not in the community repository.")
        desc.set_wrap(True)
        group.add(desc)

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(10)
        row = 0
        grid.attach(Gtk.Label(label="Package name:", xalign=0), 0, row, 1, 1)
        self.app.new_name_entry = Gtk.Entry()
        grid.attach(self.app.new_name_entry, 1, row, 1, 1)
        row += 1
        grid.attach(Gtk.Label(label="Version (e.g. 1.0):", xalign=0), 0, row, 1, 1)
        self.app.new_ver_entry = Gtk.Entry()
        grid.attach(self.app.new_ver_entry, 1, row, 1, 1)
        row += 1
        grid.attach(Gtk.Label(label="Source URL:", xalign=0), 0, row, 1, 1)
        self.app.new_url_entry = Gtk.Entry()
        grid.attach(self.app.new_url_entry, 1, row, 1, 1)
        row += 1
        grid.attach(Gtk.Label(label="Description:", xalign=0), 0, row, 1, 1)
        self.app.new_desc_entry = Gtk.Entry()
        grid.attach(self.app.new_desc_entry, 1, row, 1, 1)
        row += 1
        grid.attach(Gtk.Label(label="Dependencies (space-separated):", xalign=0), 0, row, 1, 1)
        self.app.new_deps_entry = Gtk.Entry()
        grid.attach(self.app.new_deps_entry, 1, row, 1, 1)
        group.add(grid)

        create_btn = Gtk.Button(label="Create Recipe")
        create_btn.connect("clicked", self._on_create_recipe)
        group.add(create_btn)

        page.add(group)
        return page

    def _on_create_recipe(self, widget):
        name = self.app.new_name_entry.get_text().strip()
        if not name:
            self._show_message("Error", "Package name is required.")
            return
        version = self.app.new_ver_entry.get_text().strip() or "1.0"
        url = self.app.new_url_entry.get_text().strip()
        desc = self.app.new_desc_entry.get_text().strip() or "Custom recipe"
        deps = self.app.new_deps_entry.get_text().strip()
        recipe_path = f"{LOCAL_RECIPES_DIR}/{name}.sh"
        os.makedirs(LOCAL_RECIPES_DIR, exist_ok=True)
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
            self._show_message("Success", f"Recipe {name}.sh created.")
        except Exception as e:
            self._show_message("Error", f"Failed to create recipe: {e}")

    def _show_message(self, title, msg):
        dialog = Gtk.MessageDialog(
            transient_for=self.app.window, modal=True,
            message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=msg
        )
        dialog.set_title(title)
        dialog.show()
        dialog.connect("response", lambda d, r: d.destroy())


    def _update_summary(self):
        self._collect_state()
        text = "Power User Build Summary:\n\n"
        for key, value in sorted(self.app.state.items()):
            if key not in ['LUKS_PASS', 'USER_PASS', 'ROOT_PASS']:
                text += f"{key}: {value}\n"
        self.app.summary_text.get_buffer().set_text(text)

    def _collect_state(self):
        self.app.collect_state_common()

        if hasattr(self.app, 'profile_combo'):
            values = ["default", "safe", "performance", "hardened"]
            idx = self.app.profile_combo.get_selected()
            self.app.state['POWERUSER_PROFILE'] = values[idx] if 0 <= idx < len(values) else "default"
            if hasattr(self.app, 'custom_cflags'):
                self.app.state['ARTIX_CFLAGS'] = self.app.custom_cflags
                self.app.state['ARTIX_CXXFLAGS'] = self.app.custom_cxxflags
                self.app.state['ARTIX_LDFLAGS'] = self.app.custom_ldflags
                self.app.state['ARTIX_MAKEFLAGS'] = self.app.custom_makeflags

        if hasattr(self, 'section_checkboxes'):
            sections = [sec for sec, cb in self.section_checkboxes.items() if cb.get_active()]
            self.recipe_sections = set(sections)
            self.save_sections()

        if hasattr(self.app, 'package_checkboxes'):
            selected = [name for name, cb in self.app.package_checkboxes.items() if cb.get_active()]
            self.app.state['POWERUSER_PACKAGES'] = " ".join(selected)

        if hasattr(self.app, 'coreutils_combo'):
            cu = ["gnu", "busybox", "uutils", "artix", "custom", "none"]
            self.app.state['COREUTILS'] = cu[self.app.coreutils_combo.get_selected()]
        if hasattr(self.app, 'keep_binary_switch'):
            self.app.state['KEEP_BINARY_KERNEL'] = "yes" if self.app.keep_binary_switch.get_active() else "no"

        if hasattr(self.app, 'depth_combo'):
            depth_values = ["localmodconfig", "auto", "manual", "menuconfig"]
            self.app.state['KERNEL_CONFIG_DEPTH'] = depth_values[self.app.depth_combo.get_selected()]

        for attr, key in [('gpu_checkboxes', 'KERNEL_ADV_GPU'), ('net_checkboxes', 'KERNEL_ADV_NET'),
                          ('fs_checkboxes', 'KERNEL_ADV_FS'), ('snd_checkboxes', 'KERNEL_ADV_SOUND'),
                          ('usb_checkboxes', 'KERNEL_ADV_USB'), ('sec_checkboxes', 'KERNEL_ADV_SECURITY'),
                          ('virt_checkboxes', 'KERNEL_ADV_VIRT'), ('dbg_checkboxes', 'KERNEL_ADV_DEBUG')]:
            if hasattr(self.app, attr):
                checks = getattr(self.app, attr)
                selected = [k for k, cb in checks.items() if cb.get_active()]
                self.app.state[key] = " ".join(selected)

        if hasattr(self.app, 'preempt_combo'):
            self.app.state['KERNEL_PREEMPT'] = ["voluntary", "full", "rt"][self.app.preempt_combo.get_selected()]
        if hasattr(self.app, 'timer_combo'):
            self.app.state['KERNEL_TIMER'] = ["100", "250", "300", "1000"][self.app.timer_combo.get_selected()]
        if hasattr(self.app, 'gov_combo'):
            self.app.state['KERNEL_GOVERNOR'] = ["schedutil", "ondemand", "performance"][self.app.gov_combo.get_selected()]

        self.app.state['POWER_USER'] = "yes"
        self.app.state['MODE'] = 'power'
        self.app.state['GUI_MODE'] = 'yes'

    def _on_install(self):
        self._collect_state()
        self.app.save_state()
        self.app.start_installation("Power User Installation")