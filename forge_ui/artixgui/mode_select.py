#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import sys
import os
from gi.repository import Gtk
from .automatic import AutomaticWindow
from .manual import ManualWindow
from .poweruser import PowerUserWindow
from .recovery import RecoveryWindow
from .iso import ISOBuilderWindow
from .migration import MigrationWindow
from .resume import ResumeWindow


def run_mode_selection(state_file):
    win = Gtk.Window(title="Select Installation Mode")
    win.set_default_size(500, 380)
    win.connect("destroy", lambda *_: None)

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
    cancel_btn.connect("clicked", lambda b: sys.exit(0))
    btn_box.append(cancel_btn)

    start_btn = Gtk.Button(label="Start")
    start_btn.add_css_class("suggested-action")
    btn_box.append(start_btn)

    vbox.append(btn_box)

    chosen_mode = [modes[0]]

    def on_start(btn):
        row = listbox.get_selected_row()
        if row:
            chosen_mode[0] = modes[row.get_index()]
        win.destroy()

    start_btn.connect("clicked", on_start)

    win.show()

    chosen = chosen_mode[0]

    print(f"DEBUG: Chosen mode: {chosen}", file=sys.stderr)
    sys.stderr.flush()

    state = {}
    if chosen == "Automatic Installation":
        window = AutomaticWindow(state_file, state)
    elif chosen == "Manual Installation":
        window = ManualWindow(state_file, state)
    elif chosen == "Power User Installation":
        window = PowerUserWindow(state_file, state)
    elif chosen == "System Recovery":
        window = RecoveryWindow(state_file, state)
    elif chosen == "Build ISO":
        window = ISOBuilderWindow(state_file, state)
    elif chosen == "System Migration":
        window = MigrationWindow(state_file, state)
    elif chosen == "Resume Installation":
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        state[key] = value.strip('"').replace('\\"', '"')
        window = ResumeWindow(state_file, state)
    else:
        raise ValueError(f"(MODESELECT.py) Unknown chosen variable: {chosen}")

    print(f"DEBUG: About to open {chosen} window", file=sys.stderr)
    sys.stderr.flush()
    window.run()
    print(f"DEBUG: Window closed", file=sys.stderr)
    sys.stderr.flush()