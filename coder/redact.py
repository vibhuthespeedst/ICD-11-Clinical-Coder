import os
import re

LABELLED = re.compile(
    r"(?im)^(\s*(?:patient\s+name|name|mrn|ip\s*no|op\s*no|id\s*no|national\s+id|nin|nhif(?:\s*no)?|dob|date\s+of\s+birth"
    r"|tel|phone|mobile|address|next\s+of\s+kin)\s*[:#]\s*).+$"
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?<![\w/.])\+?\d(?:[\s-]?\d){8,}(?![\w/]|\.\d)")
LONG_ID = re.compile(r"(?<![\w/.])\d{8,}(?![\w/]|\.\d)")
DATE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-](?:\d{4}|\d{2})|\d{4}-\d{2}-\d{2})\b")
TITLED = re.compile(r"\b(Mr|Mrs|Ms|Miss|Mx|Dr)(\.?\s+)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?")
SELF_NAMED = re.compile(r"((?i:my name is)\s+)[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?")


def redact(text):
    """Strip direct identifiers before a note leaves the machine; clinical values are left alone."""
    if os.environ.get("CODER_REDACT", "1") == "0":
        return text
    text = LABELLED.sub(r"\1[REDACTED]", text)
    text = EMAIL.sub("[EMAIL]", text)
    text = PHONE.sub("[PHONE]", text)
    text = LONG_ID.sub("[ID]", text)
    text = DATE.sub("[DATE]", text)
    text = TITLED.sub(r"\1\2[NAME]", text)
    return SELF_NAMED.sub(r"\1[NAME]", text)
