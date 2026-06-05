# forge-ui

Unified TUI/GUI library for ArtixForge and Volk's Forge Framework (VFF).

Provides a single command-line interface that renders either a **Textual-based terminal UI** or a **GTK3 graphical interface**, depending on the user's environment. All widgets share the same JSON input/output contract, allowing Bash scripts (ArtixForge) and Python applications (VFF) to share the same UI backend.

---

## Installation

### Install from source

```bash
git clone https://github.com/realvolk/forge-ui.git
cd forge-ui
pip install -e .
```

### Install from a local package

```bash
pip install .
```

---

## Quick Start

### Display a menu

```bash
forge-ui --mode auto <<< '{"widget":"menu","title":"Init","message":"Choose:","choices":["openrc","runit"]}'
```

### Ask a yes/no question

```bash
forge-ui <<< '{"widget":"yesno","title":"Proceed?","message":"Continue?"}'
```

### Text input with validation

```bash
forge-ui <<< '{"widget":"input","title":"Username","message":"Enter name:","default":"artix","validation":"^[a-z][a-z0-9]*$"}'
```

---

## Supported Widgets

| Widget      | Description                           |
| ----------- | ------------------------------------- |
| `menu`      | Single-selection list                 |
| `yesno`     | Boolean question                      |
| `input`     | Free-form text entry                  |
| `password`  | Masked text entry                     |
| `checklist` | Multi-selection list                  |
| `msg`       | Informational message                 |
| `summary`   | Scrollable text block                 |
| `progress`  | Live command output with progress bar |

All widgets accept JSON via `stdin` or `--input <file>` and return JSON to `stdout`.

---

## Modes

### `--mode auto` (default)

Prefer GUI if `$DISPLAY` is set, otherwise TUI.

### `--mode tui`

Force terminal UI (Textual).

### `--mode gui`

Force graphical UI (GTK3).

---

## Integration

ArtixForge replaces its Gum-based `tui_*` functions with simple wrappers that call `forge-ui`. No other scripts need to change.

---

## License

OpenVolk License 1.0 (see `LICENSE` file).

A broader OSI-approved license may be adopted in the future.
