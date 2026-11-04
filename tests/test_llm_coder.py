import json
import unittest

from coder.llm_coder import LLMCoder, Router
from coder.offline import OfflineCoder

OFFLINE = OfflineCoder()


class Fatal(Exception):
    pass


class Stub:
    name = "stub"
    model = "stub"

    def __init__(self, extract, choose, fail=None):
        self.extract, self.choose, self.fail = extract, choose, fail

    def complete(self, system, user, schema):
        if self.fail:
            raise self.fail
        return (self.extract if "code_guesses" in schema["properties"] else self.choose), 0.001

    @staticmethod
    def is_fatal(err):
        return isinstance(err, Fatal)


NOTE = "S: 28M fever, chills. BS for MPS: P. falciparum seen. A: Uncomplicated falciparum malaria."
EXTRACT = {"language": "English", "code_guesses": ["1F40"],
           "diagnoses": [{"term": "Plasmodium falciparum malaria", "search_terms": ["falciparum malaria"], "details": "uncomplicated"}]}


class LLMCoderTest(unittest.TestCase):
    def coder(self, provider):
        return LLMCoder(OFFLINE, Router([provider], budget_usd=1.0))

    def test_shortlist_reaches_the_specific_children(self):
        cands = self.coder(Stub(EXTRACT, {"codes": []})).candidates(NOTE, EXTRACT)
        self.assertIn("1F40.Z", cands)
        self.assertIn("1F40.0", cands)

    def test_invalid_codes_are_dropped_and_parents_pushed_to_unspecified(self):
        out = self.coder(Stub(EXTRACT, {"codes": ["IGNORE PREVIOUS", "ZZ99.9", "1F40", "1F40.0"]})).predict(NOTE)
        self.assertEqual(out[:2], ["1F40.Z", "1F40.0"])
        self.assertEqual(len(out), 3)
        self.assertTrue(all(c in OFFLINE.mms for c in out))

    def test_fatal_error_disables_the_provider(self):
        router = Router([Stub(EXTRACT, {}, fail=Fatal())], budget_usd=1.0)
        self.assertIsNone(LLMCoder(OFFLINE, router).predict(NOTE))
        self.assertFalse(router.alive)

    def test_budget_stops_model_calls(self):
        router = Router([Stub(EXTRACT, {"codes": ["1F40.Z"]})], budget_usd=0.0015)
        LLMCoder(OFFLINE, router).predict(NOTE)
        self.assertFalse(router.alive)


class Flaky(Stub):
    def __init__(self, extract, choose):
        super().__init__(extract, choose)
        self.calls = 0

    def complete(self, system, user, schema):
        self.calls += 1
        raise ConnectionError("proxy unreachable")


class RouterTest(unittest.TestCase):
    def test_transient_error_falls_through_to_the_next_provider(self):
        flaky = Flaky(EXTRACT, {})
        router = Router([flaky, Stub(EXTRACT, {"codes": ["1F40.Z"]})], budget_usd=1.0)
        self.assertEqual(LLMCoder(OFFLINE, router).predict(NOTE)[0], "1F40.Z")

    def test_repeated_errors_drop_the_provider(self):
        flaky = Flaky(EXTRACT, {})
        router = Router([flaky], budget_usd=1.0, max_failures=3)
        coder = LLMCoder(OFFLINE, router)
        for _ in range(5):
            try:
                coder.predict(NOTE)
            except ConnectionError:
                pass
        self.assertEqual(flaky.calls, 3)
        self.assertFalse(router.alive)


class AnthropicModelFallbackTest(unittest.TestCase):
    def test_unavailable_model_moves_to_the_next(self):
        import os
        import anthropic
        import httpx2
        from coder.llm_anthropic import AnthropicLLM

        os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-a-key")
        llm = AnthropicLLM()
        seen = []

        class Resp:
            stop_reason = "end_turn"
            content = [type("B", (), {"type": "text", "text": '{"codes": ["1F40.Z"]}'})()]
            usage = type("U", (), {"input_tokens": 10, "output_tokens": 5})()

        def create(**kw):
            seen.append((kw["model"], "effort" in kw["output_config"]))
            if kw["model"] == "claude-haiku-5-5":
                req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
                raise anthropic.NotFoundError("model not found", response=httpx2.Response(404, request=req), body=None)
            return Resp()

        llm.client = type("C", (), {"messages": type("M", (), {"create": staticmethod(create)})()})()
        out, _ = llm.complete("s", "u", {"type": "object"})
        self.assertEqual(out, {"codes": ["1F40.Z"]})
        self.assertEqual(seen, [("claude-haiku-5-5", True), ("claude-haiku-4-5", False)])
        self.assertEqual(llm.model, "claude-haiku-4-5")


if __name__ == "__main__":
    unittest.main()
