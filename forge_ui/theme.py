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
        212: "#c678dd", 34: "#98c379", 39: "#61afef",
        245: "#928374", 250: "#a89984", 3: "#d19a66",
        117: "#56b6c2", 196: "#e06c75", 255: "#ffffff", 11: "#e5c07b",
    }
    return palette.get(code, f"#{code}")


def _lighten_hex(hex_color, factor=0.25):
    hex_color = hex_color.lstrip("#")
    r = min(255, int(int(hex_color[0:2], 16) + (255 - int(hex_color[0:2], 16)) * factor))
    g = min(255, int(int(hex_color[2:4], 16) + (255 - int(hex_color[2:4], 16)) * factor))
    b = min(255, int(int(hex_color[4:6], 16) + (255 - int(hex_color[4:6], 16)) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_dark_css(title_color, accent_color):
    t = _color_to_hex(title_color)
    a = _color_to_hex(accent_color)
    al = _lighten_hex(a)

    return f"""
    * {{
        font-family: "Cantarell", "DejaVu Sans", sans-serif;
        color: #e0e0e0;
    }}

    window {{
        background-color: #1a1a1a;
    }}

    label {{
        color: #e0e0e0;
        background-color: transparent;
    }}
    .title {{
        font-size: 22px;
        font-weight: bold;
        color: {t};
        margin-bottom: 12px;
    }}

    button {{
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        background: #2d2d2d;
        color: #f0f0f0;
        border: 1px solid #3c3c3c;
    }}
    button:hover {{
        background: #3c3c3c;
        border-color: {a};
    }}
    button.suggested-action {{
        background: {a};
        color: #1a1a1a;
        border: none;
    }}
    button.suggested-action:hover {{
        background: {al};
    }}

    entry {{
        border-radius: 6px;
        padding: 10px 12px;
        background: #2d2d2d;
        color: #f0f0f0;
        border: 1px solid #3c3c3c;
        caret-color: {a};
    }}
    entry:focus {{
        border-color: {a};
    }}

    combobox {{
        background: #2d2d2d;
        border-radius: 6px;
    }}
    combobox button {{
        border-radius: 6px;
        background: #2d2d2d;
        color: #f0f0f0;
        padding: 8px 14px;
    }}
    combobox button:hover {{
        background: #3c3c3c;
    }}
    combobox window {{
        background: #2d2d2d;
    }}
    combobox window box {{
        background: #2d2d2d;
    }}
    combobox window box label {{
        color: #f0f0f0;
        padding: 6px 12px;
    }}
    combobox window box label:hover {{
        background: {a};
        color: #1a1a1a;
    }}

    menu {{
        background: #2d2d2d;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
    }}
    menuitem {{
        padding: 8px 16px;
        color: #f0f0f0;
    }}
    menuitem:hover {{
        background: {a};
        color: #1a1a1a;
    }}

    checkbutton {{
        margin: 6px 0;
        color: #f0f0f0;
    }}
    checkbutton check {{
        border-radius: 4px;
        background: #2d2d2d;
        border: 1px solid #3c3c3c;
        min-width: 18px;
        min-height: 18px;
    }}
    checkbutton check:checked {{
        background: {a};
        border-color: {a};
    }}

    notebook {{
        background: #252525;
        border-radius: 8px;
        padding: 4px;
    }}
    notebook tab {{
        background: #2d2d2d;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        margin-right: 2px;
        color: #bbbbbb;
    }}
    notebook tab:hover {{
        background: #3c3c3c;
    }}
    notebook tab:checked {{
        background: {a};
        color: #1a1a1a;
        font-weight: bold;
    }}
    notebook > stack > box,
    notebook > stack > box > box,
    notebook viewport,
    notebook scrolledwindow {{
        background: #252525;
    }}

    scrolledwindow {{
        border-radius: 6px;
        background: #1a1a1a;
        border: 1px solid #3c3c3c;
    }}

    textview {{
        background: #1a1a1a;
        color: #e8e8e8;
        padding: 12px;
        font-family: "Monospace", "Source Code Pro", monospace;
        font-size: 13px;
    }}
    textview text {{
        background: #1a1a1a;
        color: #e8e8e8;
    }}
    textview text:selected {{
        background: {a};
        color: #1a1a1a;
    }}

    progressbar trough {{
        background: #2d2d2d;
        border-radius: 4px;
        min-height: 10px;
    }}
    progressbar progress {{
        background: {a};
        border-radius: 4px;
    }}

    frame {{
        border-radius: 8px;
        border: 1px solid #3c3c3c;
        background: #252525;
    }}

    .logview {{
        color: {a};
        background-color: #1a1a1a;
        font-family: monospace;
        padding: 8px;
    }}

    box, grid, centerbox {{
        background: transparent;
    }}
    """


def get_light_css(title_color, accent_color):
    t = _color_to_hex(title_color)
    a = _color_to_hex(accent_color)
    al = _lighten_hex(a)

    return f"""
    * {{
        font-family: "Cantarell", "DejaVu Sans", sans-serif;
        color: #1a1a1a;
    }}

    window {{
        background-color: #f5f5f5;
    }}

    label {{
        color: #1a1a1a;
        background-color: transparent;
    }}
    .title {{
        font-size: 22px;
        font-weight: bold;
        color: {t};
        margin-bottom: 12px;
    }}

    button {{
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        background: #e0e0e0;
        color: #1a1a1a;
        border: 1px solid #b0b0b0;
    }}
    button:hover {{
        background: #d0d0d0;
        border-color: {a};
    }}
    button.suggested-action {{
        background: {a};
        color: #ffffff;
        border: none;
    }}
    button.suggested-action:hover {{
        background: {al};
    }}

    entry {{
        border-radius: 6px;
        padding: 10px 12px;
        background: #ffffff;
        color: #1a1a1a;
        border: 1px solid #b0b0b0;
        caret-color: {a};
    }}
    entry:focus {{
        border-color: {a};
    }}

    combobox {{
        background: #ffffff;
        border-radius: 6px;
    }}
    combobox button {{
        border-radius: 6px;
        background: #ffffff;
        color: #1a1a1a;
        padding: 8px 14px;
    }}
    combobox button:hover {{
        background: #e0e0e0;
    }}
    combobox window {{
        background: #ffffff;
    }}
    combobox window box {{
        background: #ffffff;
    }}
    combobox window box label {{
        color: #1a1a1a;
        padding: 6px 12px;
    }}
    combobox window box label:hover {{
        background: {a};
        color: #ffffff;
    }}

    menu {{
        background: #ffffff;
        border: 1px solid #b0b0b0;
        border-radius: 6px;
    }}
    menuitem {{
        padding: 8px 16px;
        color: #1a1a1a;
    }}
    menuitem:hover {{
        background: {a};
        color: #ffffff;
    }}

    checkbutton {{
        margin: 6px 0;
        color: #1a1a1a;
    }}
    checkbutton check {{
        border-radius: 4px;
        background: #e0e0e0;
        border: 1px solid #b0b0b0;
        min-width: 18px;
        min-height: 18px;
    }}
    checkbutton check:checked {{
        background: {a};
        border-color: {a};
    }}

    notebook {{
        background: #ffffff;
        border-radius: 8px;
        padding: 4px;
    }}
    notebook tab {{
        background: #e0e0e0;
        border-radius: 6px 6px 0 0;
        padding: 10px 20px;
        margin-right: 2px;
        color: #1a1a1a;
    }}
    notebook tab:hover {{
        background: #d0d0d0;
    }}
    notebook tab:checked {{
        background: {a};
        color: #ffffff;
        font-weight: bold;
    }}
    notebook > stack > box,
    notebook > stack > box > box,
    notebook viewport,
    notebook scrolledwindow {{
        background: #ffffff;
    }}

    scrolledwindow {{
        border-radius: 6px;
        background: #ffffff;
        border: 1px solid #b0b0b0;
    }}

    textview {{
        background: #ffffff;
        color: #1a1a1a;
        padding: 12px;
        font-family: "Monospace", "Source Code Pro", monospace;
        font-size: 13px;
    }}
    textview text {{
        background: #ffffff;
        color: #1a1a1a;
    }}
    textview text:selected {{
        background: {a};
        color: #ffffff;
    }}

    progressbar trough {{
        background: #e0e0e0;
        border-radius: 4px;
        min-height: 10px;
    }}
    progressbar progress {{
        background: {a};
        border-radius: 4px;
    }}

    frame {{
        border-radius: 8px;
        border: 1px solid #b0b0b0;
        background: #ffffff;
    }}

    .logview {{
        color: {a};
        background-color: #f5f5f5;
        font-family: monospace;
        padding: 8px;
    }}

    box, grid, centerbox {{
        background: transparent;
    }}
    """

def get_global_css(title_color, accent_color, *, light=False):
    if light:
        return get_light_css(title_color, accent_color)
    return get_dark_css(title_color, accent_color)