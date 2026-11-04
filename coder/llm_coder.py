import os
import re
import sys
import threading

from . import prompts
from .text import weighted_query, tokens

CODE_SHAPE = re.compile(r"^[0-9A-Z]{4}(\.[0-9A-Z]{1,3})?$")


def make_providers():
    providers = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from .llm_anthropic import AnthropicLLM
            providers.append(AnthropicLLM())
        except Exception as e:
            print(f"anthropic client unavailable: {e}", file=sys.stderr)
    if os.environ.get("OPENAI_API_KEY"):
        try:
            from .llm_openai import OpenAILLM
            providers.append(OpenAILLM())
        except Exception as e:
            print(f"openai client unavailable: {e}", file=sys.stderr)
    return providers


class Router:
    """Tries providers in order; drops one for good on an auth or model error."""

    def __init__(self, providers, budget_usd):
        self.providers = list(providers)
        self.budget = budget_usd
        self.spent = 0.0
        self.lock = threading.Lock()

    @property
    def alive(self):
        return bool(self.providers) and self.spent < self.budget

    def complete(self, system, user, schema):
        for p in list(self.providers):
            try:
                out, cost = p.complete(system, user, schema)
            except Exception as e:
                if p.is_fatal(e):
                    print(f"{p.name}: disabled after {type(e).__name__}", file=sys.stderr)
                    with self.lock:
                        if p in self.providers:
                            self.providers.remove(p)
                    continue
                raise
            with self.lock:
                self.spent += cost
            return out
        return None


class LLMCoder:
    def __init__(self, offline, router, max_candidates=90):
        self.offline = offline
        self.mms = offline.mms
        self.router = router
        self.max_candidates = max_candidates

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
        extracted = self.router.complete(prompts.EXTRACT_SYSTEM, prompts.extract_prompt(note), prompts.EXTRACT_SCHEMA)
        if not extracted:
            return None
        cands = self.candidates(note, extracted)
        chosen = self.router.complete(
            prompts.CHOOSE_SYSTEM, prompts.choose_prompt(note, extracted, self.render(cands)), prompts.CHOOSE_SCHEMA
        )
        out = []
        raw = (chosen or {}).get("codes", []) or extracted.get("code_guesses", [])
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
