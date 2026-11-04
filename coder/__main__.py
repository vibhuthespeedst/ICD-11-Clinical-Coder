import json
import os
import sys

from .offline import FALLBACK, OfflineCoder


def read_notes(path):
    notes = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                n = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in n:
                notes.append({"id": n["id"], "text": str(n.get("text") or "")})
    return notes


def write_predictions(path, notes, preds):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for n in notes:
            f.write(json.dumps({"id": n["id"], "codes": preds.get(n["id"]) or FALLBACK}, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def main(argv):
    if len(argv) != 3:
        sys.exit("usage: coder IN.jsonl OUT.jsonl")
    notes = read_notes(argv[1])
    os.makedirs(os.path.dirname(os.path.abspath(argv[2])), exist_ok=True)
    coder = OfflineCoder()
    preds = {}
    for n in notes:
        try:
            preds[n["id"]] = coder.predict(n["text"])
        except Exception as e:
            print(f"{n['id']}: offline coder failed: {e}", file=sys.stderr)
    write_predictions(argv[2], notes, preds)
    print(f"wrote {len(notes)} predictions to {argv[2]}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
