#!/usr/bin/env python3
import sys
sys.path = [p for p in sys.path if p != '']

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pathlib
pkg_dir = pathlib.Path(__file__).resolve().parent
for pyc in pkg_dir.rglob('*.pyc'):
    try:
        pyc.unlink()
    except OSError:
        pass
for cachedir in pkg_dir.rglob('__pycache__'):
    try:
        for f in cachedir.iterdir():
            f.unlink()
        cachedir.rmdir()
    except OSError:
        pass

import json
import argparse
from .theme import get_colors
from .schema import validate
from .backends.gui import GuiBackend


def main():
    parser = argparse.ArgumentParser(description="GTK3 GUI frontend")
    parser.add_argument("--mode", choices=["auto", "gui", "config"], default="auto",
                        help="Display mode: config = persistent configuration window, gui = single widget, auto = gui if DISPLAY set")
    parser.add_argument("--input", "-i", type=argparse.FileType("r"),
                        default=sys.stdin, help="Input JSON file (stdin if omitted)")
    parser.add_argument("--output", "-o", type=argparse.FileType("w"),
                        default=sys.stdout, help="Output JSON file (stdout if omitted)")
    parser.add_argument("--color-title", type=int, default=None,
                        help="Title color (256-color code)")
    parser.add_argument("--color-accent", type=int, default=None,
                        help="Accent color (256-color code)")
    args = parser.parse_args()

    if args.mode == "config":
        state_file = "/tmp/artix-installer/state.conf"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        try:
            from .artixgui.mode_select import run_mode_selection
            run_mode_selection(state_file)
        except Exception as e:
            print(f"GUI mode selection failed: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    try:
        raw = args.input.read()
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as e:
        json.dump({"error": f"Invalid input JSON: {e}", "cancelled": True}, args.output)
        sys.exit(1)

    try:
        data = validate(data)
    except Exception as e:
        json.dump({"error": str(e), "cancelled": True}, args.output)
        sys.exit(1)

    title_color, accent_color = get_colors(args.color_title, args.color_accent)

    if args.mode == "gui" or (args.mode == "auto" and os.environ.get("DISPLAY")):
        backend = GuiBackend()
    else:
        json.dump({"error": "No DISPLAY available – cannot start GUI", "cancelled": True}, args.output)
        sys.exit(1)

    try:
        result = backend.run(data, title_color=title_color, accent_color=accent_color)
    except Exception as e:
        result = {"error": str(e), "cancelled": True}

    json.dump(result, sys.stderr)
    sys.stderr.flush()


if __name__ == "__main__":
    main()