#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
import sys
from gi.repository import Gtk, Gdk
from .automatic import AutomaticWindow
from .manual import ManualWindow
from .poweruser import PowerUserWindow
from .recovery import RecoveryWindow
from .iso import ISOBuilderWindow
from .migration import MigrationWindow
from .resume import ResumeWindow
from ..theme import get_global_css

def run_mode_selection(state_file):
    dialog = Gtk.Dialog(title="Select Installation Mode",
                        parent=None,
                        flags=Gtk.DialogFlags.MODAL)
    dialog.set_default_size(500, 280)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Start", Gtk.ResponseType.OK)

    css = get_global_css(212, 34)
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode())
    Gtk.StyleContext.add_provider_for_screen(
        dialog.get_screen(), provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    content = dialog.get_content_area()
    content.set_spacing(10)
    content.set_margin_top(20)
    content.set_margin_start(20)
    content.set_margin_end(20)
    content.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))

    label = Gtk.Label()
    label.set_markup('<span size="large" weight="bold">Choose installation mode:</span>')
    content.pack_start(label, False, False, 0)

    mode_store = Gtk.ListStore(str)
    modes = [
        "Automatic Installation",
        "Manual Installation",
        "Power User Installation",
        "System Recovery",
        "Build ISO",
        "System Migration",
        "Resume Installation"
    ]
    for mode in modes:
        mode_store.append([mode])

    mode_combo = Gtk.ComboBox.new_with_model(mode_store)
    renderer = Gtk.CellRendererText()
    renderer.set_property("foreground", "#f0f0f0")
    mode_combo.pack_start(renderer, True)
    mode_combo.add_attribute(renderer, "text", 0)
    mode_combo.set_active(0)
    mode_combo.set_size_request(380, -1)
    content.pack_start(mode_combo, False, False, 0)

    response = dialog.run()
    if response != Gtk.ResponseType.OK:
        dialog.destroy()
        sys.exit(0)

    idx = mode_combo.get_active()
    chosen = modes[idx] if 0 <= idx < len(modes) else "Automatic Installation"
    dialog.destroy()

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
        window = ResumeWindow(state_file, state)
    else:
        window = AutomaticWindow(state_file, state)

    window.run()