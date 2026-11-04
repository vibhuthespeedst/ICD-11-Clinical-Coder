"""Build data/icd10-to-icd11.json from WHO's mapping.zip (ICD-11 2026-01 release files).
Usage: python -I scripts/build_icd10_map.py <folder with the extracted .txt files>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rows(path):
    raw = path.read_bytes()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    lines = raw.decode(enc).splitlines()
    head = lines[0].split("\t")
    i10, i11, kind = head.index("icd10Code"), head.index("icd11Code"), head.index("10ClassKind")
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) > max(i10, i11) and f[kind] == "category" and f[i10] and f[i11]:
            yield f[i10].strip().upper(), f[i11].strip().upper().split("&")[0].split("/")[0]


def main():
    folder = Path(sys.argv[1])
    valid = {r["code"] for r in json.loads((ROOT / "data" / "mms-2026-01.json").read_text(encoding="utf-8"))}
    out = {}
    for name in ["10To11MapToOneCategory.txt", "10To11MapToMultipleCategories.txt"]:
        for c10, c11 in rows(folder / name):
            if c11 in valid and c11 not in out.setdefault(c10, []):
                out[c10].append(c11)
    out = {k: v for k, v in sorted(out.items()) if v}
    dest = ROOT / "data" / "icd10-to-icd11.json"
    dest.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} ICD-10 codes mapped, {sum(map(len, out.values()))} targets -> {dest}")


if __name__ == "__main__":
    main()
