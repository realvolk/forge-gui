#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
import os
import sys
from gi.repository import Gtk

from .base import InstallerApp


class ArtixForgeDispatcher:
    """Legacy dispatcher – kept for compatibility with direct imports.
       The new code path uses InstallerApp directly from cli.py."""
    def __init__(self, state_file):
        self.state_file = state_file
        self.state = {}
        self.load_state()
        self.mode = self.state.get("MODE", "auto")

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            value = value.strip('"').replace('\\"', '"')
                            self.state[key] = value
            except Exception as e:
                print(f"Warning: Could not load state: {e}")

    def run(self):
        app = InstallerApp(self.state_file)
        app.state = self.state
        app.run()


def run_dispatcher(state_file):
    dispatcher = ArtixForgeDispatcher(state_file)
    dispatcher.run()