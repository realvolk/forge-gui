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
    css = get_global_css(title_color=212, accent_color=34)
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    dialog = Gtk.Dialog(title="Select Installation Mode",
                        parent=None,
                        flags=Gtk.DialogFlags.MODAL)
    dialog.set_default_size(450, 220)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Start", Gtk.ResponseType.OK)

    content = dialog.get_content_area()
    content.set_spacing(10)
    content.set_margin_top(20)
    content.set_margin_start(20)
    content.set_margin_end(20)

    label = Gtk.Label()
    label.set_markup('<span size="large" weight="bold" foreground="#e0e0e0">Choose installation mode:</span>')
    content.pack_start(label, False, False, 0)

    mode_combo = Gtk.ComboBoxText()
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
        mode_combo.append_text(mode)
    mode_combo.set_active(0)
    mode_combo.set_size_request(350, -1)
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