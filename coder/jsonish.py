import json

INSTRUCTION = "\n\nReply with only one JSON object that matches this JSON Schema:\n"


def parse_json(text):
    """A JSON object from model text that may carry code fences or a sentence around it."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise
        return json.loads(text[start:end + 1])
