import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


class MMS:
    def __init__(self, path=DATA / "mms-2026-01.json"):
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
        self.rows = {r["code"]: r for r in rows}
        self.parent = {}
        self.children = {}
        for code in self.rows:
            p = self._find_parent(code)
            if p:
                self.parent[code] = p
                self.children.setdefault(p, []).append(code)

    def _find_parent(self, code):
        c = code
        while len(c) > 4:
            c = c[:-1].rstrip(".")
            if c in self.rows:
                return c
        return None

    def __contains__(self, code):
        return code in self.rows

    def title(self, code):
        return self.rows[code]["title"]

    def is_leaf(self, code):
        return self.rows[code]["leaf"]

    def ancestors(self, code):
        out = []
        while code in self.parent:
            code = self.parent[code]
            out.append(code)
        return out

    def leaves_under(self, code):
        if self.is_leaf(code):
            return [code]
        out = []
        for c in self.children.get(code, []):
            out.extend(self.leaves_under(c))
        return out

    def unspecified_child(self, code):
        for c in self.children.get(code, []):
            if c.endswith("Z") and self.rows[c]["residual"]:
                return c
        return None
