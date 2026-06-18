#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
import os
import sys
from gi.repository import Gtk

from .automatic import AutomaticWindow
from .manual import ManualWindow
from .resume import ResumeWindow
from .recovery import RecoveryWindow
from .poweruser import PowerUserWindow
from .iso import ISOBuilderWindow
from .migration import MigrationWindow

class ArtixForgeDispatcher:
    def __init__(self, state_file):
        self.state_file = state_file
        self.state = {}
        self.load_state()
        self.mode = self.state.get("MODE", "auto")
        
        # Route to appropriate window
        if self.mode == "auto":
            self.window = AutomaticWindow(state_file, self.state)
        elif self.mode == "manual":
            self.window = ManualWindow(state_file, self.state)
        elif self.mode == "resume":
            self.window = ResumeWindow(state_file, self.state)
        elif self.mode == "recovery":
            self.window = RecoveryWindow(state_file, self.state)
        elif self.mode == "power":
            self.window = PowerUserWindow(state_file, self.state)
        elif self.mode == "iso":
            self.window = ISOBuilderWindow(state_file, self.state)
        elif self.mode == "migrate":
            self.window = MigrationWindow(state_file, self.state)
        else:
            self.window = AutomaticWindow(state_file, self.state)
    
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
        self.window.run()

def run_dispatcher(state_file):
    dispatcher = ArtixForgeDispatcher(state_file)
    dispatcher.run()