import json

from .mms import DATA


def load_terms():
    """Extra search terms per code from WHO files in data/who/, if any were downloaded."""
    terms = {}
    folder = DATA / "who"
    if not folder.is_dir():
        return terms
    for path in sorted(folder.glob("mms-*-*.json"), key=lambda p: (not p.stem.endswith("-en"), p.name)):
        lang = path.stem.rsplit("-", 1)[-1]
        for code, e in json.loads(path.read_text(encoding="utf-8")).items():
            extra = list(e.get("index", [])) + list(e.get("inclusion", []))
            if lang != "en" and e.get("title"):
                extra.append(e["title"])
            if extra:
                terms.setdefault(code, []).extend(extra)
    return terms
