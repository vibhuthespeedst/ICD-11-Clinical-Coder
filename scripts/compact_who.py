"""Shrink fetch_who.py output for the repo: English keeps every field, other languages keep title and index terms.
Usage: python -I scripts/compact_who.py <folder with mms-2026-01-<lang>.json files>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    rows = json.loads((ROOT / "data" / "mms-2026-01.json").read_text(encoding="utf-8"))
    uri_code = {r["uri"].replace("/release/11/mms/", "/release/11/2026-01/mms/"): r["code"] for r in rows}
    out_dir = ROOT / "data" / "who"
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(Path(sys.argv[1]).rglob("mms-2026-01-*.json")):
        lang = src.stem.rsplit("-", 1)[-1]
        out = {}
        for code, e in json.loads(src.read_text(encoding="utf-8")).items():
            title = e.get("title", "")
            index = [t for t in e.get("index", []) if t.casefold() != title.casefold()]
            entry = {"index": index} if index else {}
            if lang != "en":
                entry["title"] = title
            else:
                if e.get("inclusion"):
                    entry["inclusion"] = e["inclusion"]
                excl = [[x["label"], uri_code.get(x.get("ref", ""), "")] for x in e.get("exclusion", [])]
                if excl:
                    entry["exclusion"] = excl
                for key in ("definition", "codingNote"):
                    if e.get(key):
                        entry[key] = e[key]
            if entry:
                out[code] = entry
        dest = out_dir / src.name
        dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        print(f"{dest.name}: {len(out)} codes, {dest.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
