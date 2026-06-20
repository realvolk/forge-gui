# forge-gui

GTK4 graphical frontend for ArtixForge and Volk's Forge Framework (VFF).

Provides a single command-line interface that renders a **GTK4 window** for all user interactions. All widgets share the same JSON input/output contract, allowing Bash scripts (ArtixForge) and Python applications (VFF) to use a consistent GUI backend.

---

## Installation

### Install from Source

```bash
git clone https://github.com/realvolk/forge-gui.git
cd forge-gui
pip install -e .
```

### System Dependencies

#### Artix Linux

```bash
sudo pacman -S gtk4 libadawaita python-gobject
```

---

## Quick Start

### Display a Menu

```bash
forge-gui --mode gui <<< '{"widget":"menu","title":"Init","message":"Choose:","choices":["openrc","runit"]}'
```

### Ask a Yes/No Question

```bash
forge-gui --mode gui <<< '{"widget":"yesno","title":"Proceed?","message":"Continue?"}'
```

### Text Input with Validation

```bash
forge-gui --mode gui <<< '{"widget":"input","title":"Username","message":"Enter name:","default":"artix"}'
```

---

## Supported Widgets

| Widget | Description |
|---------|-------------|
| `menu` | Single-selection list |
| `yesno` | Boolean question |
| `input` | Free-form text entry |
| `password` | Masked text entry |
| `checklist` | Multi-selection list |
| `msg` | Informational message |
| `summary` | Scrollable text block |
| `progress` | Live command output with progress bar |

All widgets accept JSON via `stdin` or `--input <file>` and return JSON to `stderr`.

---

## Modes

### `--mode gui`

Force graphical UI (GTK4). Requires `$DISPLAY` to be set.

### `--mode auto` (default)

Same as `--mode gui` (legacy, kept for compatibility).

### `--mode config` (special case)

Launches the persistent configuration window for ArtixForge installation.
This is the mode used by the ArtixForge installer when a graphical
environment is detected.

---

## Integration with ArtixForge

ArtixForge detects `$DISPLAY` and calls `forge-gui` for all interactive prompts, replacing the TUI. The same JSON contract allows seamless switching between terminal and graphical installers.

---

## License

Forge Attribution License 1.0 (see `LICENSE` file).