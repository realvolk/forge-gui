import os

# Default colors (Gentoo theme)
DEFAULT_TITLE = 212
DEFAULT_ACCENT = 34

def get_colors(title=None, accent=None):
    """Resolve title and accent colors from args or env."""
    title = title or os.environ.get("GUM_TITLE_COLOR", DEFAULT_TITLE)
    accent = accent or os.environ.get("GUM_ACCENT_COLOR", DEFAULT_ACCENT)
    return int(title), int(accent)

def ansi_color(code):
    """Return ANSI escape for 256-color foreground."""
    return f"\033[38;5;{code}m"

def reset():
    return "\033[0m"

# Alignment mapping for Textual
ALIGN_MAP = {
    "left": "left",
    "center": "center",
    "right": "right",
    "top-left": "left",
    "top-center": "center",
    "top-right": "right",
}