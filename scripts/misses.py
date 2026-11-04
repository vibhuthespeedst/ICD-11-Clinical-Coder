"""Print each miss from score.py --per-note output: gold vs predicted titles and the note's diagnosis line.
Usage: python scripts/misses.py out/dev.per-note.jsonl data/dev_notes.jsonl
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DX = re.compile(r"(?im)^\s*(?:a|ax|dx|imp|impression|assessment|diagnosis)\s*[:\-].*$|\bdx\b[^.\n]*")


def main():
    per_note, notes_path = sys.argv[1], sys.argv[2]
    titles = {r["code"]: r["title"] for r in json.loads((ROOT / "data" / "mms-2026-01.json").read_text(encoding="utf-8"))}
    notes = {n["id"]: n for n in map(json.loads, open(notes_path, encoding="utf-8")) if n}
    rows = [json.loads(l) for l in open(per_note, encoding="utf-8") if l.strip()]
    top3_only = [r for r in rows if r["top3"] and not r["top1"]]
    misses = [r for r in rows if not r["top3"]]
    for label, group in (("right code only in slots 2-3", top3_only), ("no right code in top 3", misses)):
        print(f"== {label}: {len(group)}")
        for r in group:
            text = notes.get(r["id"], {}).get("text", "")
            m = DX.search(text)
            hint = (m.group(0) if m else text[-160:]).replace("\n", " ")[:140]
            gold = "; ".join(f"{c} {titles.get(c, '?')}" for c in r["gold"])
            pred = " | ".join(f"{c} {titles.get(c, '?')[:40]}" for c in r["pred"] if c)
            print(f"{r['id']}  gold: {gold}\n    pred: {pred}\n    note: {hint}")


if __name__ == "__main__":
    main()
