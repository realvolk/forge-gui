import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

import json
import sys
import subprocess
import threading
import re
import os
from gi.repository import Gtk, GLib, Adw, Gdk, Pango


class BaseWindow:
    """Shared setup for standalone widgets."""

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
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_key)
        self.window.add_controller(key_controller)
        self.window.connect("destroy", self._on_destroy)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        vbox.set_valign(Gtk.Align.CENTER)
        self.window.set_child(vbox)

        if self.title_text:
            title_label = Gtk.Label(label=self.title_text)
            title_label.add_css_class("title-1")
            title_label.set_halign(Gtk.Align.CENTER)
            vbox.append(title_label)

        if self.message:
            msg_label = Gtk.Label(label=self.message)
            msg_label.set_halign(Gtk.Align.CENTER)
            msg_label.set_wrap(True)
            msg_label.set_max_width_chars(60)
            vbox.append(msg_label)

        return vbox

    def _on_key(self, controller, keyval, keycode, state):
        if keyval == Gtk.KEY_Escape:
            self.cancelled = True
            self.window.destroy()
        return False

    def _on_destroy(self, widget):
        if not getattr(self, '_finished', False):
            self.cancelled = True

    def _quit(self):
        self.window.destroy()

    def _make_button_box(self, *buttons):
        box = Gtk.Box(spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        for label, cb, primary in buttons:
            btn = Gtk.Button(label=label)
            if primary:
                btn.add_css_class("suggested-action")
            btn.connect("clicked", cb)
            box.append(btn)
        return box

    def run(self):
        self.window.show()
        loop = GLib.MainLoop()
        self.window.connect("destroy", lambda *_: loop.quit())
        loop.run()
        return {"result": self.result, "cancelled": self.cancelled}


class MenuWindow(BaseWindow):
    def run(self):
        choices = self.data.get("choices", [])
        default = self.data.get("default", "")

        vbox = self._create_window(500, min(len(choices) * 35 + 150, 600))

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.set_vexpand(True)

        for choice in choices:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=choice, xalign=0, margin_top=5, margin_bottom=5)
            row.set_child(label)
            listbox.append(row)
            if choice == default:
                listbox.select_row(row)

        listbox.connect("row-activated", lambda lb, row: self._select(row))
        vbox.append(listbox)

        vbox.append(self._make_button_box(("Cancel", lambda b: self._cancel(), False)))

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
        vbox.append(
            self._make_button_box(
                ("Yes", lambda b: self._answer(True), True),
                ("No",  lambda b: self._answer(False), False),
            )
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
        vbox.append(self.entry)

        vbox.append(
            self._make_button_box(
                ("OK", lambda b: self._submit(), True),
                ("Cancel", lambda b: self._cancel(), False),
            )
        )
        self.window.show()
        self.entry.grab_focus()
        loop = GLib.MainLoop()
        self.window.connect("destroy", lambda *_: loop.quit())
        loop.run()
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
        self.entry = Gtk.PasswordEntry()
        self.entry.set_show_peek_icon(False)
        if self.data.get("placeholder"):
            self.entry.set_placeholder_text(self.data["placeholder"])
        self.entry.connect("activate", lambda e: self._submit())
        vbox.append(self.entry)

        vbox.append(
            self._make_button_box(
                ("OK", lambda b: self._submit(), True),
                ("Cancel", lambda b: self._cancel(), False),
            )
        )
        self.window.show()
        self.entry.grab_focus()
        loop = GLib.MainLoop()
        self.window.connect("destroy", lambda *_: loop.quit())
        loop.run()
        return {"result": self.result or "", "cancelled": self.cancelled}


class ChecklistWindow(BaseWindow):
    def run(self):
        choices = self.data.get("choices", [])
        defaults = set(self.data.get("default", []))

        vbox = self._create_window(500, min(len(choices) * 35 + 150, 600))

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._checks = []

        for choice in choices:
            row = Gtk.ListBoxRow()
            check = Gtk.CheckButton(label=choice)
            check.set_active(choice in defaults)
            row.set_child(check)
            listbox.append(row)
            self._checks.append(check)

        vbox.append(listbox)
        vbox.append(
            self._make_button_box(
                ("OK", lambda b: self._ok(), True),
                ("Cancel", lambda b: self._cancel(), False),
            )
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
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda b: self._quit())
        vbox.append(btn)
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
        scrolled.set_child(textview)
        vbox.append(scrolled)
        return super().run()


class ProgressWindow(BaseWindow):
    def _create_window(self, default_w=800, default_h=600):
        self.window = Gtk.Window(title=self.title_text or "forge-ui")
        self.window.set_default_size(default_w, default_h)
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_key)
        self.window.add_controller(key_controller)
        self.window.connect("destroy", self._on_destroy)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        vbox.set_valign(Gtk.Align.FILL)
        vbox.set_vexpand(True)
        self.window.set_child(vbox)

        if self.title_text:
            title_label = Gtk.Label(label=self.title_text)
            title_label.add_css_class("title-1")
            title_label.set_halign(Gtk.Align.CENTER)
            vbox.append(title_label)

        if self.message:
            msg_label = Gtk.Label(label=self.message)
            msg_label.set_halign(Gtk.Align.CENTER)
            msg_label.set_wrap(True)
            msg_label.set_max_width_chars(60)
            vbox.append(msg_label)

        return vbox

    def run(self):
        vbox = self._create_window(800, 600)

        app = Gtk.Application.get_default()
        if app:
            app.add_window(self.window)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.log_view.set_hexpand(True)
        self.log_view.set_vexpand(True)
        self.log_view.add_css_class("logview")

        scrolled.set_child(self.log_view)
        vbox.append(scrolled)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_fraction(0.0)
        vbox.append(self.progress_bar)

        self.spinner = Gtk.Spinner()
        self.spinner.start()
        vbox.append(self.spinner)

        vbox.append(
            self._make_button_box(("Cancel", lambda b: self._cancel(), False))
        )

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
        .logview {
            font-family: monospace;
            padding: 8px;
        }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.success = True
        self._proc = None
        self._finished = False
        self.window.show()
        threading.Thread(target=self._run_command, daemon=True).start()

        loop = GLib.MainLoop()
        self.window.connect("destroy", lambda *_: loop.quit())
        loop.run()

        return {"result": "success" if self.success else "failure",
                "cancelled": self.cancelled}

    def _run_command(self):
        cmd = self.data.get("command", [])
        state = self.data.get("state", {})
        
        stages = [
            ("preflight", "Preflight dependencies installed", 0.05),
            ("storage", "Mount setup completed", 0.10),
            ("partition", "Partitioning complete", 0.15),
            ("filesystem", "Filesystem creation complete", 0.20),
            ("base", "Base system installation complete", 0.35),
        ]
        if state.get("POWER_USER") == "yes":
            stages.append(("poweruser", "All source packages built and installed", 0.55))
        stages += [
            ("chroot", "Bootloader setup complete", 0.55 if state.get("POWER_USER") != "yes" else 0.70),
            ("init", "BusyBox init configuration complete", 0.60 if state.get("POWER_USER") != "yes" else 0.75),
            ("post", "Post-install configuration complete", 0.85),
            ("finalize", "Artix installation completed successfully", 0.95),
        ]
        
        stage_match = {msg: prog for _, msg, prog in stages}
        current = 0.0
        
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in self._proc.stdout:
            GLib.idle_add(self._append_log, line)
            for msg, prog in stage_match.items():
                if msg in line:
                    current = max(current, prog)
                    GLib.idle_add(self.progress_bar.set_fraction, current)
                    break
        self._proc.wait()
        self.success = self._proc.returncode == 0
        GLib.idle_add(self._done)

    def _append_log(self, line):
        clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
        clean = re.sub(r'\[[0-9;]*m', '', clean)
        clean = re.sub(r'\[[0-9;]*K', '', clean)
        clean = ''.join(c for c in clean if c.isprintable() or c in '\n\r\t ')
        buf = self.log_view.get_buffer()
        buf.insert(buf.get_end_iter(), clean)
        self.log_view.scroll_to_iter(buf.get_end_iter(), 0.0, False, 0.0, 0.0)

    def _done(self):
        self.spinner.stop()
        self.progress_bar.set_fraction(1.0)
        self._finished = True
        self.window.destroy()

    def _cancel(self):
        self.cancelled = True
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self.window.destroy()


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