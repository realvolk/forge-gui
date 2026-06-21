#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import os
from gi.repository import Gtk, GLib
from .automatic import AutomaticWindow
from .manual import ManualWindow
from .poweruser import PowerUserWindow
from .recovery import RecoveryWindow
from .iso import ISOBuilderWindow
from .migration import MigrationWindow
from .resume import ResumeWindow


class ModeSelectApp(Gtk.Application):
    def __init__(self, state_file):
        super().__init__(application_id="com.artixforge.mode-select")
        self.state_file = state_file

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title="Select Installation Mode")
        win.set_default_size(500, 380)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        win.set_child(vbox)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Choose installation mode:</span>')
        vbox.append(label)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

        modes = [
            "Automatic Installation",
            "Manual Installation",
            "Power User Installation",
            "System Recovery",
            "Build ISO",
            "System Migration",
            "Resume Installation"
        ]

        for i, mode in enumerate(modes):
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=mode, xalign=0, margin_top=8, margin_bottom=8)
            row.set_child(lbl)
            listbox.append(row)
            if i == 0:
                listbox.select_row(row)

        scrolled.set_child(listbox)
        vbox.append(scrolled)

        btn_box = Gtk.Box(spacing=10)
        btn_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: self.quit())
        btn_box.append(cancel_btn)

        start_btn = Gtk.Button(label="Start")
        start_btn.add_css_class("suggested-action")
        btn_box.append(start_btn)

        vbox.append(btn_box)

        def on_start(btn):
            row = listbox.get_selected_row()
            if row:
                chosen = modes[row.get_index()]
                win.destroy()
                self._launch_config(chosen)

        start_btn.connect("clicked", on_start)
        win.show()

    def _launch_config(self, chosen):
        state = {}
        preserve_modes = ["Resume Installation", "System Recovery", "System Migration"]
        if chosen not in preserve_modes:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        if chosen == "Resume Installation":
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            state[key] = value.strip('"').replace('\\"', '"')

        window_classes = {
            "Automatic Installation": AutomaticWindow,
            "Manual Installation": ManualWindow,
            "Power User Installation": PowerUserWindow,
            "System Recovery": RecoveryWindow,
            "Build ISO": ISOBuilderWindow,
            "System Migration": MigrationWindow,
            "Resume Installation": ResumeWindow,
        }
        cls = window_classes.get(chosen)
        if cls is None:
            self.quit()
            return

        self.hold()
        config_win = cls(self.state_file, state)
        config_win.app = self
        config_win.run()
        self.release()
        self.quit()


def run_mode_selection(state_file):
    app = ModeSelectApp(state_file)
    app.run()