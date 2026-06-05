import jsonschema

WIDGET_SCHEMAS = {
    "menu": {
        "type": "object",
        "properties": {
            "widget": {"const": "menu"},
            "title": {"type": "string"},
            "message": {"type": "string"},
            "choices": {"type": "array", "items": {"type": "string"}},
            "height": {"type": "integer"},
            "default": {"type": "string"},
            "align": {"type": "string"},
        },
        "required": ["widget", "choices"],
    },
    "yesno": {
        "type": "object",
        "properties": {
            "widget": {"const": "yesno"},
            "title": {"type": "string"},
            "message": {"type": "string"},
            "default": {"type": "boolean"},
        },
        "required": ["widget"],
    },
    "input": {
        "type": "object",
        "properties": {
            "widget": {"const": "input"},
            "title": {"type": "string"},
            "message": {"type": "string"},
            "default": {"type": "string"},
            "placeholder": {"type": "string"},
            "validation": {"type": "string"},
        },
        "required": ["widget"],
    },
    "password": {
        "type": "object",
        "properties": {
            "widget": {"const": "password"},
            "title": {"type": "string"},
            "message": {"type": "string"},
            "placeholder": {"type": "string"},
        },
        "required": ["widget"],
    },
    "checklist": {
        "type": "object",
        "properties": {
            "widget": {"const": "checklist"},
            "title": {"type": "string"},
            "message": {"type": "string"},
            "choices": {"type": "array", "items": {"type": "string"}},
            "height": {"type": "integer"},
            "min": {"type": "integer"},
            "max": {"type": "integer"},
            "default": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["widget", "choices"],
    },
    "msg": {
        "type": "object",
        "properties": {
            "widget": {"const": "msg"},
            "title": {"type": "string"},
            "message": {"type": "string"},
        },
        "required": ["widget", "message"],
    },
    "summary": {
        "type": "object",
        "properties": {
            "widget": {"const": "summary"},
            "title": {"type": "string"},
            "message": {"type": "string"},
            "file": {"type": "string"},
        },
        "required": ["widget"],
    },
    "progress": {
        "type": "object",
        "properties": {
            "widget": {"const": "progress"},
            "title": {"type": "string"},
            "command": {"type": "array", "items": {"type": "string"}},
            "logfile": {"type": "string"},
        },
        "required": ["widget", "command"],
    },
}


def validate(data):
    """Validate input JSON against the widget schema. Raises on error."""
    widget = data.get("widget")
    if widget not in WIDGET_SCHEMAS:
        raise ValueError(f"Unknown widget: {widget}")
    jsonschema.validate(instance=data, schema=WIDGET_SCHEMAS[widget])
    return data