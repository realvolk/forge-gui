import json
import sys
import subprocess
import threading
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, Pango


def _color_to_hex(code):
    """Convert 256-color code to approximate hex for GTK CSS."""
    # Standard 256-color palette mapping (common values)
    palette = {
        212: "#c678dd",  # gentoo purple
        34:  "#98c379",  # gentoo green
        39:  "#61afef",  # artix blue
        245: "#928374", # grey
        250: "#a89984", # light grey
        3:   "#d19a66", # amber
        117: "#56b6c2", # baby blue
        196: "#e06c75", # red
        255: "#ffffff", # white
        11:  "#e5c07b", # yellow
    }
    return palette.get(code, f"#{code}")


class BaseWindow:
    """Shared setup: window creation, title, message, escape-to-cancel."""

    def __init__(self, data, title_color, accent_color):
        self.data = data
        self.title_text = data.get("title", "")
        self.message = data.get("message", "")
        self._title_color = title_color
        self._accent_color = accent_color
        self.result = None
        self.cancelled = False
        self.window = None

    def _create_window(self, default_w=600, default_h=400):
        self.window = Gtk.Window(title=self.title_text or "forge-ui")
        self.window.set_default_size(default_w, default_h)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("key-press-event", self._on_key)
        self.window.connect("destroy", self._on_destroy)

        css = f"""
        .title {{ font-size: 18px; font-weight: bold; color: {_color_to_hex(self._title_color)}; }}
        .accent {{ color: {_color_to_hex(self._accent_color)}; }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(20)
        vbox.set_valign(Gtk.Align.CENTER)
        self.window.add(vbox)

        if self.title_text:
            title_label = Gtk.Label(label=self.title_text)
            title_label.get_style_context().add_class("title")
            title_label.set_halign(Gtk.Align.CENTER)
            vbox.pack_start(title_label, False, False, 0)

        if self.message:
            msg_label = Gtk.Label(label=self.message)
            msg_label.set_halign(Gtk.Align.CENTER)
            msg_label.set_line_wrap(True)
            msg_label.set_max_width_chars(60)
            vbox.pack_start(msg_label, False, False, 10)

        return vbox

    def _on_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.cancelled = True
            self.window.destroy()

    def _on_destroy(self, widget):
        self.cancelled = True

    def _quit(self):
        self.window.destroy()
        Gtk.main_quit()

    def _make_button_box(self, *buttons):
        box = Gtk.Box(spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        for label, cb, primary in buttons:
            btn = Gtk.Button(label=label)
            if primary:
                btn.get_style_context().add_class("suggested-action")
            btn.connect("clicked", cb)
            box.pack_start(btn, False, False, 0)
        return box

    def run(self):
        self.window.show_all()
        Gtk.main()
        return {"result": self.result, "cancelled": self.cancelled}

class MenuWindow(BaseWindow):
    def run(self):
        choices = self.data.get("choices", [])
        default = self.data.get("default", "")
        
        item_height = 35  # pixels per row
        window_height = min(len(choices) * item_height + 150, 600)  # cap at 600
        vbox = self._create_window(500, window_height)
        
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        for choice in choices:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=choice, xalign=0, margin=5)
            row.add(label)
            listbox.add(row)
            if choice == default:
                listbox.select_row(row)
        
        listbox.connect("row-activated", lambda lb, row: self._select(row))
        vbox.pack_start(listbox, True, True, 0)
        
        vbox.pack_start(
            self._make_button_box(("Cancel", lambda b: self._cancel(), False)),
            False, False, 10
        )
        
        return super().run()
    
    def _select(self, row):
        self.result = row.get_child().get_text()
        self._quit()
    
    def _cancel(self):
        self.cancelled = True
        self._quit()

class YesNoWindow(BaseWindow):
    def run(self):
        vbox = self._create_window(400, 200)
        vbox.pack_start(
            self._make_button_box(
                ("Yes", lambda b: self._answer(True), True),
                ("No",  lambda b: self._answer(False), False),
            ),
            False, False, 20
        )
        return super().run()

    def _answer(self, val):
        self.result = val
        self._quit()

class InputWindow(BaseWindow):
    def run(self):
        vbox = self._create_window(500, 200)
        self.entry = Gtk.Entry()
        self.entry.set_text(self.data.get("default", ""))
        if self.data.get("placeholder"):
            self.entry.set_placeholder_text(self.data["placeholder"])
        self.entry.connect("activate", lambda e: self._submit())
        vbox.pack_start(self.entry, False, False, 10)

        vbox.pack_start(
            self._make_button_box(
                ("OK", lambda b: self._submit(), True),
                ("Cancel", lambda b: self._cancel(), False),
            ),
            False, False, 10
        )
        self.window.show_all()
        self.entry.grab_focus()
        Gtk.main()
        return {"result": self.result or "", "cancelled": self.cancelled}

    def _submit(self):
        self.result = self.entry.get_text()
        self._quit()

    def _cancel(self):
        self.cancelled = True
        self._quit()

class PasswordWindow(InputWindow):
    def run(self):
        vbox = self._create_window(500, 200)
        self.entry = Gtk.Entry()
        self.entry.set_visibility(False)
        self.entry.set_invisible_char("*")
        if self.data.get("placeholder"):
            self.entry.set_placeholder_text(self.data["placeholder"])
        self.entry.connect("activate", lambda e: self._submit())
        vbox.pack_start(self.entry, False, False, 10)

        vbox.pack_start(
            self._make_button_box(
                ("OK", lambda b: self._submit(), True),
                ("Cancel", lambda b: self._cancel(), False),
            ),
            False, False, 10
        )
        self.window.show_all()
        self.entry.grab_focus()
        Gtk.main()
        return {"result": self.result or "", "cancelled": self.cancelled}

class ChecklistWindow(BaseWindow):
    def run(self):
        choices = self.data.get("choices", [])
        defaults = set(self.data.get("default", []))
        
        # Calculate window height dynamically
        item_height = 35  # pixels per row
        window_height = min(len(choices) * item_height + 150, 600)  # cap at 600
        vbox = self._create_window(500, window_height)
        
        listbox = Gtk.ListBox()
        self._checks = []
        
        for choice in choices:
            row = Gtk.ListBoxRow()
            check = Gtk.CheckButton(label=choice)
            check.set_active(choice in defaults)
            row.add(check)
            listbox.add(row)
            self._checks.append(check)
        
        vbox.pack_start(listbox, True, True, 0)
        vbox.pack_start(
            self._make_button_box(
                ("OK", lambda b: self._ok(), True),
                ("Cancel", lambda b: self._cancel(), False),
            ),
            False, False, 10
        )
        return super().run()
    
    def _ok(self):
        self.result = [c.get_label() for c in self._checks if c.get_active()]
        self._quit()
    
    def _cancel(self):
        self.cancelled = True
        self._quit()

class MsgWindow(BaseWindow):
    def run(self):
        vbox = self._create_window(400, 200)
        btn = Gtk.Button(label="OK")
        btn.get_style_context().add_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda b: self._quit())
        vbox.pack_start(btn, False, False, 10)
        return super().run()

class SummaryWindow(BaseWindow):
    def run(self):
        vbox = self._create_window(650, 500)
        text = self.message or ""
        file_path = self.data.get("file")
        if file_path:
            try:
                with open(file_path, "r") as f:
                    text = f.read()
            except Exception:
                text = f"[Error reading {file_path}]"

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.get_buffer().set_text(text)
        textview.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(textview)
        vbox.pack_start(scrolled, True, True, 0)
        return super().run()

class ProgressWindow(BaseWindow):
    def _create_window(self, default_w=800, default_h=600):
        """Override to use FILL alignment for progress window."""
        self.window = Gtk.Window(title=self.title_text or "forge-ui")
        self.window.set_default_size(default_w, default_h)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("key-press-event", self._on_key)
        self.window.connect("destroy", self._on_destroy)

        css = f"""
        .title {{ font-size: 18px; font-weight: bold; color: {_color_to_hex(self._title_color)}; }}
        .accent {{ color: {_color_to_hex(self._accent_color)}; }}
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(20)
        vbox.set_valign(Gtk.Align.FILL)
        vbox.set_vexpand(True)
        self.window.add(vbox)

        if self.title_text:
            title_label = Gtk.Label(label=self.title_text)
            title_label.get_style_context().add_class("title")
            title_label.set_halign(Gtk.Align.CENTER)
            vbox.pack_start(title_label, False, False, 0)

        if self.message:
            msg_label = Gtk.Label(label=self.message)
            msg_label.set_halign(Gtk.Align.CENTER)
            msg_label.set_line_wrap(True)
            msg_label.set_max_width_chars(60)
            vbox.pack_start(msg_label, False, False, 10)

        return vbox

    def run(self):
        vbox = self._create_window(800, 600)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.set_hexpand(True)
        self.log_view.set_vexpand(True)
        
        # Use a monospace font for logs
        font = Pango.FontDescription("monospace 10")
        self.log_view.modify_font(font)
        
        scrolled.add(self.log_view)
        vbox.pack_start(scrolled, True, True, 0)
        
        self.spinner = Gtk.Spinner()
        self.spinner.start()
        vbox.pack_start(self.spinner, False, False, 5)
        
        vbox.pack_start(
            self._make_button_box(("Cancel", lambda b: self._cancel(), False)),
            False, False, 10
        )

        self.success = True
        self._proc = None
        self.window.show_all()
        threading.Thread(target=self._run_command, daemon=True).start()
        Gtk.main()
        return {"result": "success" if self.success else "failure",
                "cancelled": self.cancelled}

    def _run_command(self):
        cmd = self.data.get("command", [])
        logfile = self.data.get("logfile")
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in self._proc.stdout:
            GLib.idle_add(self._append_log, line)
            if logfile:
                with open(logfile, "a") as f:
                    f.write(line)
        self._proc.wait()
        self.success = self._proc.returncode == 0
        GLib.idle_add(self._done)

    def _append_log(self, line):
        buf = self.log_view.get_buffer()
        buf.insert(buf.get_end_iter(), line)
        # Auto-scroll to bottom
        self.log_view.scroll_to_iter(buf.get_end_iter(), 0.0, False, 0.0, 0.0)

    def _done(self):
        self.spinner.stop()
        self._quit()

    def _cancel(self):
        self.cancelled = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._quit()

class GuiBackend:
    def run(self, data, title_color=212, accent_color=34):
        widget = data["widget"]
        cls_map = {
            "menu": MenuWindow,
            "yesno": YesNoWindow,
            "input": InputWindow,
            "password": PasswordWindow,
            "checklist": ChecklistWindow,
            "msg": MsgWindow,
            "summary": SummaryWindow,
            "progress": ProgressWindow,
        }
        cls = cls_map.get(widget)
        if cls is None:
            return {"result": "", "cancelled": True}
        return cls(data, title_color, accent_color).run()