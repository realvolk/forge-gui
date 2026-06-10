import os

DEFAULT_TITLE = 212
DEFAULT_ACCENT = 34

def get_colors(title=None, accent=None):
    title = title or os.environ.get("GUM_TITLE_COLOR", DEFAULT_TITLE)
    accent = accent or os.environ.get("GUM_ACCENT_COLOR", DEFAULT_ACCENT)
    return int(title), int(accent)

def ansi_color(code):
    return f"\033[38;5;{code}m"

def reset():
    return "\033[0m"

def _color_to_hex(code):
    palette = {
        212: "#c678dd", 34:  "#98c379", 39:  "#61afef",
        245: "#928374", 250: "#a89984", 3:   "#d19a66",
        117: "#56b6c2", 196: "#e06c75", 255: "#ffffff", 11: "#e5c07b",
    }
    return palette.get(code, f"#{code}")

def _lighten_hex(hex_color, factor=0.2):
    hex_color = hex_color.lstrip('#')
    r = min(255, int(int(hex_color[0:2], 16) + (255 - int(hex_color[0:2], 16)) * factor))
    g = min(255, int(int(hex_color[2:4], 16) + (255 - int(hex_color[2:4], 16)) * factor))
    b = min(255, int(int(hex_color[4:6], 16) + (255 - int(hex_color[4:6], 16)) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"

def get_global_css(title_color, accent_color):
    """Return the full GTK3 CSS stylesheet as a string."""
    title_hex = _color_to_hex(title_color)
    accent_hex = _color_to_hex(accent_color)
    accent_light = _lighten_hex(accent_hex)

    return f"""
    * {{
        font-family: "Cantarell", "DejaVu Sans", sans-serif;
        background-color: transparent;
    }}
    window {{
        background-color: #1e1e1e;
    }}
    .title {{
        font-size: 24px;
        font-weight: bold;
        color: {title_hex};
        margin-bottom: 12px;
    }}
    button {{
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: bold;
        background: #2d2d2d;
        color: #eeeeee;
        border: 1px solid #3c3c3c;
    }}
    button:hover {{
        background: #3c3c3c;
        border-color: {accent_hex};
    }}
    button.suggested-action {{
        background: {accent_hex};
        color: #1e1e1e;
        border: none;
    }}
    button.suggested-action:hover {{
        background: {accent_light};
    }}
    entry {{
        border-radius: 6px;
        padding: 8px 10px;
        background: #2d2d2d;
        color: #eeeeee;
        border: 1px solid #3c3c3c;
    }}
    entry:focus {{
        border-color: {accent_hex};
    }}
    combobox {{
        border-radius: 6px;
        background: #2d2d2d;
    }}
    combobox button {{
        border-radius: 6px;
        background: #2d2d2d;
        color: #eeeeee;
        padding: 6px 12px;
    }}
    combobox button:hover {{
        background: #3c3c3c;
    }}
    menu {{
        background: #2d2d2d;
        border: 1px solid #3c3c3c;
    }}
    menuitem {{
        padding: 6px 12px;
        color: #eeeeee;
    }}
    menuitem:hover {{
        background: {accent_hex};
        color: #1e1e1e;
    }}
    checkbutton {{
        margin: 4px 0;
        color: #eeeeee;
    }}
    checkbutton check {{
        border-radius: 4px;
        background: #2d2d2d;
        border: 1px solid #3c3c3c;
        min-width: 16px;
        min-height: 16px;
    }}
    checkbutton check:checked {{
        background: {accent_hex};
        border-color: {accent_hex};
    }}
    checkbutton:hover check {{
        border-color: {accent_hex};
    }}
    notebook {{
        background: #252525;
        border-radius: 8px;
        padding: 4px;
    }}
    notebook tab {{
        background: #2d2d2d;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        margin-right: 2px;
        color: #bbbbbb;
    }}
    notebook tab:hover {{
        background: #3c3c3c;
    }}
    notebook tab:checked {{
        background: {accent_hex};
        color: #1e1e1e;
        font-weight: bold;
    }}
    notebook tab:checked:hover {{
        background: {accent_light};
    }}
    scrolledwindow {{
        border-radius: 6px;
        background: #1e1e1e;
    }}
    scrolledwindow .frame {{
        border: 1px solid #3c3c3c;
        border-radius: 6px;
    }}
    textview {{
        background: #1e1e1e;
        color: #d0d0d0;
        padding: 8px;
        font-family: "Monospace", "Source Code Pro", monospace;
        font-size: 12px;
    }}
    textview text {{
        background: #1e1e1e;
        color: #d0d0d0;
    }}
    textview text:selected {{
        background: {accent_hex};
        color: #1e1e1e;
    }}
    progressbar {{
        min-height: 8px;
    }}
    progressbar trough {{
        background: #2d2d2d;
        border-radius: 4px;
        min-height: 8px;
    }}
    progressbar progress {{
        background: {accent_hex};
        border-radius: 4px;
    }}
    spinner {{
        color: {accent_hex};
    }}
    frame {{
        border-radius: 8px;
        border: 1px solid #3c3c3c;
        background: #252525;
    }}
    separator {{
        background-color: #3c3c3c;
    }}
    box, grid, centerbox {{
        background: transparent;
    }}
    .logview {{
        color: {accent_hex};
        background-color: #1a1a1a;
        font-family: monospace;
        padding: 8px;
    }}
    """