import hashlib
import json
import os
import random
import re
import sys
import threading
import time

from . import prompts
from .mms import DATA
from .redact import redact
from .text import weighted_query, tokens

CODE_SHAPE = re.compile(r"^[0-9A-Z]{4}(\.[0-9A-Z]{1,3})?$")
ICD10_SHAPE = re.compile(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,2})?$")


def load_icd10_map():
    path = DATA / "icd10-to-icd11.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def map_icd10(table, code):
    c = re.sub(r"[^0-9A-Z.]", "", str(code).upper())
    if len(c) > 3 and "." not in c:
        c = c[:3] + "." + c[3:]
    if not ICD10_SHAPE.match(c):
        return []
    return table.get(c) or table.get(c[:3]) or []


class Cached:
    """Dev-only: replays a provider's earlier answer for an identical request (CODER_CACHE_DIR)."""

    def __init__(self, inner, folder):
        self.inner, self.folder = inner, folder
        self.name = inner.name
        self.is_fatal = inner.is_fatal
        self.is_transient = getattr(inner, "is_transient", lambda e: False)
        os.makedirs(folder, exist_ok=True)

    @property
    def model(self):
        return self.inner.model

    def complete(self, system, user, schema):
        blob = json.dumps([self.inner.name, self.inner.model, system, user, schema], sort_keys=True)
        path = os.path.join(self.folder, hashlib.sha256(blob.encode("utf-8")).hexdigest() + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f), 0.0
        out, cost = self.inner.complete(system, user, schema)
        if out is not None:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f)
        return out, cost


def make_providers():
    providers = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from .llm_anthropic import AnthropicLLM
            providers.append(AnthropicLLM())
        except Exception as e:
            print(f"anthropic client unavailable: {describe(e)}", file=sys.stderr)
    if os.environ.get("OPENAI_API_KEY"):
        try:
            from .llm_openai import OpenAILLM
            providers.append(OpenAILLM())
        except Exception as e:
            print(f"openai client unavailable: {describe(e)}", file=sys.stderr)
    cache = os.environ.get("CODER_CACHE_DIR")
    if cache and providers:
        print(f"dev cache on: model answers are stored in {cache}; never use it with real patient notes", file=sys.stderr)
    return [Cached(p, cache) for p in providers] if cache else providers


def describe(err):
    """Error type and HTTP status only: provider error bodies can echo parts of the note."""
    status = getattr(err, "status_code", None)
    return type(err).__name__ + (f" {status}" if status else "")


class Throttle:
    """Caps calls in flight: halves the cap on a rate limit, adds one back after cap-many successes."""

    def __init__(self, limit):
        self.max = self.limit = max(1, limit)
        self.active = self.ok = 0
        self.cond = threading.Condition()

    def __enter__(self):
        with self.cond:
            while self.active >= self.limit:
                self.cond.wait(timeout=1.0)
            self.active += 1

    def __exit__(self, *exc):
        with self.cond:
            self.active -= 1
            self.cond.notify_all()

    def slow_down(self):
        with self.cond:
            old, self.limit, self.ok = self.limit, max(1, self.limit // 2), 0
        if self.limit != old:
            print(f"rate limited: at most {self.limit} calls in flight", file=sys.stderr)

    def success(self):
        with self.cond:
            self.ok += 1
            if self.limit < self.max and self.ok >= self.limit:
                self.limit, self.ok = self.limit + 1, 0
                self.cond.notify_all()


class Router:
    """Tries providers in order. Rate limits and 5xx back off and retry; an auth error, or
    max_failures other errors in a row, drops the provider for the rest of the run."""

    def __init__(self, providers, budget_usd, max_failures=10, max_inflight=12, deadline=None, retries=6, backoff=1.0):
        self.providers = list(providers)
        self.budget = budget_usd
        self.max_failures = max_failures
        self.deadline = deadline
        self.retries = retries
        self.backoff = backoff
        self.throttle = Throttle(max_inflight)
        self.spent = 0.0
        self.failures = {}
        self.lock = threading.Lock()

    @property
    def alive(self):
        return bool(self.providers) and self.spent < self.budget

    def _drop(self, p, why):
        with self.lock:
            if p in self.providers:
                self.providers.remove(p)
                print(f"{p.name}: disabled ({why})", file=sys.stderr)

    def _call(self, p, system, user, schema):
        transient = getattr(p, "is_transient", lambda e: False)
        for attempt in range(self.retries):
            try:
                with self.throttle:
                    return p.complete(system, user, schema)
            except Exception as e:
                if not transient(e) or attempt == self.retries - 1:
                    raise
                self.throttle.slow_down()
                wait = min(30.0, self.backoff * 2.0 ** attempt) * random.uniform(0.5, 1.0)
                if self.deadline is not None and time.monotonic() + wait > self.deadline:
                    raise
                time.sleep(wait)

    def complete(self, system, user, schema):
        last = None
        for p in list(self.providers):
            try:
                out, cost = self._call(p, system, user, schema)
            except Exception as e:
                if p.is_fatal(e):
                    self._drop(p, type(e).__name__)
                    continue
                last = e
                if getattr(p, "is_transient", lambda e: False)(e):
                    continue
                with self.lock:
                    n = self.failures[p.name] = self.failures.get(p.name, 0) + 1
                if n >= self.max_failures:
                    self._drop(p, f"{n} errors in a row, last {type(e).__name__}")
                continue
            self.throttle.success()
            with self.lock:
                self.spent += cost
                self.failures[p.name] = 0
            return out
        if last is not None:
            raise last
        return None


class LLMCoder:
    def __init__(self, offline, router, max_candidates=90):
        self.offline = offline
        self.mms = offline.mms
        self.router = router
        self.max_candidates = max_candidates
        self.icd10 = load_icd10_map()

    def clean_code(self, code):
        c = str(code).strip().upper().split("&")[0].split("/")[0]
        return c if CODE_SHAPE.match(c) and c in self.mms else None

    def family(self, code, cap=40):
        stem = code[:4]
        if stem not in self.mms:
            return [code]
        fam = [stem] + [c for c in self.mms.leaves_under(stem) if c != stem]
        return fam[:cap]

    def candidates(self, note, extracted):
        picked = []

        def add(codes):
            for c in codes:
                if c not in picked:
                    picked.append(c)

        for c10 in extracted.get("icd10_codes", []):
            for c in map_icd10(self.icd10, c10):
                add(self.family(c))
        for g in extracted.get("code_guesses", []):
            c = self.clean_code(g)
            if c:
                add(self.family(c))
        for d in extracted.get("diagnoses", []):
            for q in [d.get("term", "")] + list(d.get("search_terms", [])):
                if not tokens(q):
                    continue
                ranked, _ = self.offline.rank(q, k=6)
                for c in ranked[:4]:
                    add(self.family(c, cap=25))
        ranked, _ = self.offline.rank(note, k=8)
        for c in ranked[:5]:
            add(self.family(c, cap=15))
        return picked[: self.max_candidates]

    def render(self, codes):
        lines = []
        for c in codes:
            p = self.mms.parent.get(c)
            leaf = "" if self.mms.is_leaf(c) else " [has subcodes]"
            also = "; ".join(self.offline.terms.get(c, [])[:3])
            lines.append(f"{c} | {self.mms.title(c)}{leaf} | {self.mms.title(p) if p else '-'}" + (f" | also: {also}" if also else ""))
        return "\n".join(lines)

    def predict(self, note):
        sent = redact(note)
        extracted = self.router.complete(prompts.EXTRACT_SYSTEM, prompts.extract_prompt(sent), prompts.EXTRACT_SCHEMA)
        if not extracted:
            return None
        cands = self.candidates(note, extracted)
        chosen = self.router.complete(
            prompts.CHOOSE_SYSTEM, prompts.choose_prompt(sent, extracted, self.render(cands)), prompts.CHOOSE_SCHEMA
        )
        out = []
        mapped = [c for c10 in extracted.get("icd10_codes", []) for c in map_icd10(self.icd10, c10)]
        raw = (chosen or {}).get("codes", []) or mapped + extracted.get("code_guesses", [])
        for code in raw:
            c = self.clean_code(code)
            if not c:
                continue
            if not self.mms.is_leaf(c):
                c = self.mms.unspecified_child(c) or c
            if c not in out:
                out.append(c)
            if len(out) == 3:
                break
        for c in self.offline.predict(note):
            if len(out) == 3:
                break
            if c not in out:
                out.append(c)
        return out or None
