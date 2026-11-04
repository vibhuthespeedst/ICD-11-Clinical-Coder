"""Write synthetic notes with known codes across chapters and languages (DECISIONS.md, entry 9).
Usage: python scripts/make_synth.py --n 150  (needs a key in the environment)
"""
import argparse
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from coder.llm_coder import Router, make_providers  # noqa: E402
from coder.mms import MMS  # noqa: E402

LANGS = ["English"] * 6 + ["French", "Swahili", "Spanish", "Portuguese", "Arabic", "Hindi", "Amharic"]
STYLES = {
    "typed_consult": "a typed consult note of 100-200 words with S/O/A/P or Hx/Ex/Imp/Plan sections and clinical abbreviations",
    "short_consult": "a terse note of 2-4 lines (30-70 words) with heavy abbreviations, as a busy clinician types between patients",
    "ambient_transcript": "a transcript of 120-250 words from an ambient scribe, 'Doctor:' and 'Patient:' lines, where the doctor states the diagnosis in plain words",
}
SKIP_CHAPTERS = {"23", "25", "26"}

SYSTEM = """You write realistic outpatient clinical notes for testing a medical coding system.
Write like a real clinician: vary age, sex, setting and wording, use local or lay terms where natural,
include vitals, findings and a plan. Never write an ICD code, and do not copy the category title word for word."""

SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
    "additionalProperties": False,
}


def prompt(mms, code, lang, style):
    parent = mms.parent.get(code)
    siblings = [c for c in mms.children.get(parent, []) if c != code] if parent else []
    sib = "\n".join(f"- {mms.title(c)}" for c in siblings[:12]) or "- none"
    if code.endswith("Z"):
        rule = "The note must NOT give the detail that would separate these more specific categories:\n" + sib
    else:
        rule = "Include the clinical details that make this the right category rather than these neighbours:\n" + sib
    language = (f"Language: {lang}. Write the whole note in {lang}, including everything the doctor and patient say; "
                f"only the 'Doctor:' and 'Patient:' labels may stay in English.\n") if lang != "English" else ""
    return (
        language
        + f"Write {STYLES[style]}, in {lang}.\n"
        f"The clinician's diagnosis must fit exactly this ICD-11 category: {mms.title(code)}"
        + (f" (a kind of: {mms.title(parent)})" if parent else "")
        + f".\n{rule}"
    )


ENGLISH = set("the and with for of to in is was patient doctor no not has have you your she he his her they this that "
              "on at as are be pain fever days history plan review today".split())


SCRIPTS = {"Arabic": r"[؀-ۿ]", "Hindi": r"[ऀ-ॿ]", "Amharic": r"[ሀ-፿]"}


def mostly_english(text):
    words = re.findall(r"[a-z']+", text.lower())
    return bool(words) and sum(w in ENGLISH for w in words) / len(words) > 0.15


def wrong_language(text, lang):
    if lang in SCRIPTS:
        letters = re.findall(r"[^\W\d_]", text)
        return not letters or len(re.findall(SCRIPTS[lang], text)) / len(letters) < 0.3
    return lang != "English" and mostly_english(text)


def sample(mms, n, rng):
    by_chapter = {}
    for code, r in mms.rows.items():
        if r["leaf"] and r["chapter"] not in SKIP_CHAPTERS and not (r["residual"] and code.endswith("Y")):
            by_chapter.setdefault(r["chapter"], []).append(code)
    chapters = sorted(by_chapter)
    return [rng.choice(by_chapter[chapters[i % len(chapters)]]) for i in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default=str(ROOT / "data" / "synth" / "synth-v1.jsonl"))
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()

    providers = make_providers()
    if not providers:
        sys.exit("no API key in the environment")
    router = Router(providers, budget_usd=2.0)
    mms = MMS()
    rng = random.Random(a.seed)
    jobs = [(i, code, rng.choice(LANGS), rng.choice(list(STYLES))) for i, code in enumerate(sample(mms, a.n, rng))]

    def one(job):
        i, code, lang, style = job
        text = None
        for attempt in range(2):
            ask = prompt(mms, code, lang, style)
            if attempt:
                ask = f"Your last note was in English. Write it again entirely in {lang}; do not use English.\n" + ask
            try:
                out = router.complete(SYSTEM, ask, SCHEMA)
            except Exception as e:
                print(f"synth-{i:03d}: {type(e).__name__}", file=sys.stderr)
                return None
            text = (out or {}).get("text")
            if text and not wrong_language(text, lang):
                break
            text = None
        if not text:
            print(f"synth-{i:03d}: dropped, not written in {lang}", file=sys.stderr)
            return None
        return {"id": f"synth-{i:03d}", "text": text, "gold": [code], "slice": "B", "style": style, "lang": lang}

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as pool:
        rows = [r for r in pool.map(one, jobs) if r]
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)}/{a.n} notes to {a.out}, est. spend ${router.spent:.3f}", file=sys.stderr)


if __name__ == "__main__":
    main()
