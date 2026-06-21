import os

DEFAULT_TITLE = 212
DEFAULT_ACCENT = 34

# Accent colors for Adw.StyleManager (RGBA floats)
ACCENT_COLORS = {
    212: (0.78, 0.47, 0.87, 1.0),   # Gentoo purple
    39:  (0.38, 0.69, 0.94, 1.0),   # Artix blue
    245: (0.57, 0.51, 0.45, 1.0),   # Jet Black grey
    250: (0.66, 0.60, 0.53, 1.0),   # Mono
    3:   (0.82, 0.60, 0.40, 1.0),   # Retro amber
}

def get_colors(title=None, accent=None):
    title = title or os.environ.get("GUM_TITLE_COLOR", DEFAULT_TITLE)
    accent = accent or os.environ.get("GUM_ACCENT_COLOR", DEFAULT_ACCENT)
    return int(title), int(accent)

def ansi_color(code):
    return f"\033[38;5;{code}m"

def reset():
    return "\033[0m"