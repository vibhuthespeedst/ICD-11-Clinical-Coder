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


if __name__ == "__main__":
    unittest.main()
