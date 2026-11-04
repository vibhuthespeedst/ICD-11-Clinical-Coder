import json
import os
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from .llm_coder import LLMCoder, Router, make_providers
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
    start = time.monotonic()
    deadline = start + float(os.environ.get("CODER_TIME_BUDGET_S", "3000"))
    out_path = argv[2]
    notes = read_notes(argv[1])
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    offline = OfflineCoder()
    preds = {}
    for n in notes:
        try:
            preds[n["id"]] = offline.predict(n["text"])
        except Exception as e:
            print(f"{n['id']}: offline coder failed: {e}", file=sys.stderr)
    write_predictions(out_path, notes, preds)
    print(f"offline predictions written for {len(notes)} notes", file=sys.stderr)

    providers = make_providers()
    if not providers:
        print("no API key set: keeping offline predictions", file=sys.stderr)
        return
    router = Router(providers, float(os.environ.get("CODER_BUDGET_USD", "5.5")))
    coder = LLMCoder(offline, router)
    print(f"model path: {', '.join(f'{p.name}:{p.model}' for p in providers)}", file=sys.stderr)

    def work(n):
        if time.monotonic() > deadline or not router.alive:
            return n["id"], None
        try:
            return n["id"], coder.predict(n["text"])
        except Exception as e:
            print(f"{n['id']}: {type(e).__name__}: {e}", file=sys.stderr)
            return n["id"], None

    upgraded = 0
    pool = ThreadPoolExecutor(max_workers=int(os.environ.get("CODER_WORKERS", "12")))
    pending = {pool.submit(work, n) for n in notes}
    while pending:
        done, pending = wait(pending, timeout=max(1.0, deadline - time.monotonic()), return_when=FIRST_COMPLETED)
        changed = False
        for f in done:
            nid, codes = f.result()
            if codes:
                preds[nid] = codes
                upgraded += 1
                changed = True
        if changed:
            write_predictions(out_path, notes, preds)
        if time.monotonic() > deadline:
            print("time budget reached, stopping model calls", file=sys.stderr)
            break
    write_predictions(out_path, notes, preds)
    print(
        f"model predictions for {upgraded}/{len(notes)} notes, est. spend ${router.spent:.3f}, "
        f"{time.monotonic() - start:.0f}s",
        file=sys.stderr,
    )
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main(sys.argv)
