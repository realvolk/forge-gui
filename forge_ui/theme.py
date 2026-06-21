import os

DEFAULT_TITLE = 212
DEFAULT_ACCENT = 34

# Accent colors for Adw.StyleManager (RGBA floats)
ACCENT_COLORS = {
    34:  (0.596, 0.765, 0.475),   # #98c379
    117: (0.337, 0.714, 0.761),   # #56b6c2
    196: (0.878, 0.424, 0.459),   # #e06c75
    255: (1.000, 1.000, 1.000),   # #ffffff
    11:  (0.898, 0.753, 0.482),   # #e5c07b
}

def get_colors(title=None, accent=None):
    title = title or os.environ.get("GUM_TITLE_COLOR", DEFAULT_TITLE)
    accent = accent or os.environ.get("GUM_ACCENT_COLOR", DEFAULT_ACCENT)
    return int(title), int(accent)

def ansi_color(code):
    return f"\033[38;5;{code}m"

def reset():
    return "\033[0m"