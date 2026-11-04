"""Download WHO's index terms, inclusions and translated titles for every code in data/mms-2026-01.json.

Source, either:
  local WHO ICD-API container (no account needed):
      docker run -d -p 8382:80 -e acceptLicense=true -e include=2026-01_en whoicd/icd-api
      python scripts/fetch_who.py --base http://localhost:8382 --lang en
  or the online API, with WHO_CLIENT_ID and WHO_CLIENT_SECRET in the environment:
      python scripts/fetch_who.py --base https://id.who.int --lang en

Writes data/who/mms-2026-01-<lang>.json:
  {code: {"title", "index", "inclusion", "exclusion": [{"label", "ref"}], "definition", "codingNote"}}.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = "2026-01"
TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"


class Auth:
    def __init__(self, online):
        self.online = online
        self.value = None
        self.at = 0.0

    def header(self):
        if not self.online:
            return {}
        if not self.value or time.time() - self.at > 3000:
            body = urllib.parse.urlencode({
                "client_id": os.environ["WHO_CLIENT_ID"],
                "client_secret": os.environ["WHO_CLIENT_SECRET"],
                "scope": "icdapi_access",
                "grant_type": "client_credentials",
            }).encode()
            with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=body), timeout=30) as r:
                self.value = json.load(r)["access_token"]
            self.at = time.time()
        return {"Authorization": f"Bearer {self.value}"}


def labels(items):
    out = []
    for it in items or []:
        lab = it.get("label") if isinstance(it, dict) else None
        val = lab.get("@value") if isinstance(lab, dict) else None
        if val and val not in out:
            out.append(val)
    return out


def fetch(base, uri, lang, auth):
    path = urllib.parse.urlparse(uri).path.replace("/icd/release/11/mms/", f"/icd/release/11/{RELEASE}/mms/")
    headers = {"Accept": "application/json", "Accept-Language": lang, "API-Version": "v2", **auth.header()}
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers), timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8382")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    rows = json.loads((ROOT / "data" / "mms-2026-01.json").read_text(encoding="utf-8"))
    auth = Auth(online="id.who.int" in a.base)
    out_path = ROOT / "data" / "who" / f"mms-{RELEASE}-{a.lang}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def one(r):
        e = fetch(a.base, r["uri"], a.lang, auth)
        if not e:
            return r["code"], None
        def text(key):
            return (e.get(key) or {}).get("@value", "")

        exclusion = [
            {"label": x["label"]["@value"], "ref": x.get("linearizationReference", "")}
            for x in e.get("exclusion") or []
            if isinstance(x.get("label"), dict) and x["label"].get("@value")
        ]
        return r["code"], {
            "title": text("title"),
            "index": labels(e.get("indexTerm")),
            "inclusion": labels(e.get("inclusion")),
            "exclusion": exclusion,
            "definition": text("definition"),
            "codingNote": text("codingNote"),
        }

    result, missing = {}, 0
    with ThreadPoolExecutor(a.workers) as pool:
        for i, (code, entry) in enumerate(pool.map(one, rows), 1):
            if entry is None:
                missing += 1
            else:
                result[code] = entry
            if i % 1000 == 0:
                print(f"{i}/{len(rows)} fetched, {missing} missing", file=sys.stderr)
    out_path.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print(f"wrote {len(result)} codes to {out_path} ({missing} missing)", file=sys.stderr)


if __name__ == "__main__":
    main()
