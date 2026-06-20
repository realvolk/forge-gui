#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
from .base import BaseWindow

class ResumeWindow(BaseWindow):
    def __init__(self, state_file, state):
        super().__init__(state_file, state, title="Resume Installation")
        self.add_page("Resume", self.create_resume_page())

    def create_resume_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label()
        label.set_markup('<span size="large" weight="bold">Resume Installation</span>')
        box.append(label)

        desc = Gtk.Label()
        desc.set_text("A saved installation state was found.\n\nClick Install to continue from where it stopped.")
        desc.set_justify(Gtk.Justification.CENTER)
        box.append(desc)

        return box

    def collect_state(self):
        self.state['MODE'] = 'resume'
        self.state['GUI_MODE'] = 'yes'

    def start_installation(self):
        self.collect_state()
        self.save_state()
        self.run_installer()