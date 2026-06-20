#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
import sys
import os
from gi.repository import Gtk, Gdk
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
    win.set_position(Gtk.WindowPosition.CENTER)
    win.connect("destroy", Gtk.main_quit)

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    vbox.set_border_width(20)
    win.add(vbox)

    label = Gtk.Label()
    label.set_markup('<span size="large" weight="bold">Choose installation mode:</span>')
    vbox.pack_start(label, False, False, 0)

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
        lbl = Gtk.Label(label=mode, xalign=0, margin=8)
        row.add(lbl)
        listbox.add(row)
        if i == 0:
            listbox.select_row(row)

    scrolled.add(listbox)
    vbox.pack_start(scrolled, True, True, 0)

    btn_box = Gtk.Box(spacing=10)
    btn_box.set_halign(Gtk.Align.END)

    cancel_btn = Gtk.Button(label="Cancel")
    cancel_btn.connect("clicked", lambda b: sys.exit(0))
    btn_box.pack_start(cancel_btn, False, False, 0)

    start_btn = Gtk.Button(label="Start")
    start_btn.get_style_context().add_class("suggested-action")
    btn_box.pack_start(start_btn, False, False, 0)

    vbox.pack_start(btn_box, False, False, 0)

    chosen_mode = [modes[0]]

    def on_start(btn):
        row = listbox.get_selected_row()
        if row:
            chosen_mode[0] = modes[row.get_index()]
        win.destroy()

    start_btn.connect("clicked", on_start)

    win.show_all()
    Gtk.main()

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
                    if '=' in line:
                        key, value = line.split('=', 1)
                        state[key] = value.strip('"')
        window = ResumeWindow(state_file, state)
    else:
        raise ValueError(f"(MODESLECT.py) Unknown chosen variable: {chosen}")

    start_btn.connect("clicked", on_start)
    print(f"DEBUG: About to open {chosen} window", file=sys.stderr)
    sys.stderr.flush()
    window.run()
    print(f"DEBUG: Window closed", file=sys.stderr)
    sys.stderr.flush()