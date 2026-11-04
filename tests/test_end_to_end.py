import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.fake_api import FakeAPI

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "data" / "dev_notes.jsonl"
VALID = {r["code"] for r in json.loads((ROOT / "data" / "mms-2026-01.json").read_text(encoding="utf-8"))}
CLEAN = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_BASE_URL", "OPENAI_BASE_URL", "CODER_CACHE_DIR",
         "CODER_ANTHROPIC_MODEL", "CODER_OPENAI_MODEL", "HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy")


class EndToEndTest(unittest.TestCase):
    """Runs the real CLI and the real SDKs against a local fake API."""

    def run_cli(self, extra, notes=NOTES):
        env = {k: v for k, v in os.environ.items() if k not in CLEAN}
        env.update(extra)
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "predictions.jsonl")
            r = subprocess.run([sys.executable, "-m", "coder", str(notes), out], cwd=ROOT, env=env,
                               capture_output=True, text=True, timeout=300)
            preds = [json.loads(line) for line in open(out, encoding="utf-8")]
        return r, preds

    def check(self, r, preds):
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(preds), 60)
        self.assertTrue(all(p["codes"] and all(c in VALID for c in p["codes"]) for p in preds))
        self.assertIn("model predictions for 60/60 notes", r.stderr)

    def test_anthropic_sdk_path(self):
        api = FakeAPI()
        try:
            r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url})
        finally:
            api.close()
        self.check(r, preds)
        posts = [q for q in api.requests if q["path"].endswith("/v1/messages")]
        self.assertEqual(len(posts), 120)
        self.assertTrue(all("fake-key" in (q["headers"].get("x-api-key", ""), q["headers"].get("authorization", "")[7:]) for q in posts))
        self.assertTrue(all(q["body"]["model"] == "claude-haiku-5-5" for q in posts))
        self.assertTrue(all(q["body"]["output_config"]["format"]["type"] == "json_schema" for q in posts))

    def test_openai_sdk_path(self):
        api = FakeAPI()
        try:
            r, preds = self.run_cli({"OPENAI_API_KEY": "fake-key", "OPENAI_BASE_URL": api.url + "/v1"})
        finally:
            api.close()
        self.check(r, preds)
        posts = [q for q in api.requests if q["path"].endswith("/chat/completions")]
        self.assertEqual(len(posts), 120)
        self.assertTrue(all(q["headers"].get("authorization") == "Bearer fake-key" for q in posts))
        self.assertTrue(all(q["body"]["response_format"]["type"] == "json_schema" for q in posts))

    def test_rate_limited_requests_are_retried(self):
        api = FakeAPI(fail_first=8)
        try:
            r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url})
        finally:
            api.close()
        self.check(r, preds)
        self.assertEqual(len(api.requests), 128)


    def test_openai_steps_down_when_json_schema_is_rejected(self):
        api = FakeAPI(reject_schema=True)
        try:
            r, preds = self.run_cli({"OPENAI_API_KEY": "fake-key", "OPENAI_BASE_URL": api.url + "/v1"})
        finally:
            api.close()
        self.check(r, preds)
        posts = [q for q in api.requests if q["path"].endswith("/chat/completions")]
        self.assertEqual(posts[-1]["body"]["response_format"]["type"], "json_object")

    def test_openai_picks_the_newest_mini_model_it_has(self):
        api = FakeAPI(models=("gpt-4o", "gpt-6-mini", "gpt-5.5-mini"))
        try:
            r, preds = self.run_cli({"OPENAI_API_KEY": "fake-key", "OPENAI_BASE_URL": api.url + "/v1"})
        finally:
            api.close()
        self.check(r, preds)
        self.assertIn("openai:gpt-6-mini", r.stderr)


    def test_time_budget_stops_model_calls_and_every_note_keeps_an_answer(self):
        api = FakeAPI(delay=1.0)
        start = time.monotonic()
        try:
            r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url,
                                     "CODER_TIME_BUDGET_S": "4", "CODER_WORKERS": "4"})
        finally:
            api.close()
        elapsed = time.monotonic() - start
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(preds), 60)
        self.assertTrue(all(p["codes"] and all(c in VALID for c in p["codes"]) for p in preds))
        self.assertIn("time budget reached", r.stderr)
        self.assertNotIn("model predictions for 60/60", r.stderr)
        self.assertLess(elapsed, 30)


    def test_sustained_rate_limit_slows_down_without_losing_the_model_path(self):
        api = FakeAPI(rate_per_sec=4)
        try:
            r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url})
        finally:
            api.close()
        self.check(r, preds)
        self.assertNotIn("disabled", r.stderr)
        self.assertIn("rate limited: at most", r.stderr)
        self.assertGreater(api.rejected, 0)


    def test_anthropic_steps_down_when_structured_output_is_rejected(self):
        api = FakeAPI(reject_anthropic_format=True)
        try:
            r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url})
        finally:
            api.close()
        self.check(r, preds)
        posts = [q for q in api.requests if q["path"].endswith("/v1/messages")]
        self.assertNotIn("format", posts[-1]["body"].get("output_config", {}))
        self.assertIn("JSON Schema", json.dumps(posts[-1]["body"]["system"]))
        self.assertNotIn("disabled", r.stderr)


    def test_direct_identifiers_never_reach_the_provider(self):
        note = ("Name: Achieng Otieno\nTel: 0712 345 678\nS: 28F seen with Mrs Wanjiru Kamau, ID 12345678, DOB 12/03/1990. "
                "Fever and chills x3/7. BS for MPS: P. falciparum seen.\nA: Uncomplicated falciparum malaria.")
        api = FakeAPI()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "notes.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"id": "n1", "text": note}) + "\n")
            try:
                r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url}, notes=path)
            finally:
                api.close()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(preds[0]["codes"])
        sent = json.dumps([q["body"] for q in api.requests])
        self.assertEqual(len(api.requests), 2)
        for identifier in ("Achieng", "Otieno", "0712", "Wanjiru", "Kamau", "12345678", "12/03/1990"):
            self.assertNotIn(identifier, sent)
        self.assertIn("Uncomplicated falciparum malaria", sent)

    def test_provider_error_bodies_are_not_logged(self):
        api = FakeAPI(echo_error=True)
        try:
            r, preds = self.run_cli({"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_BASE_URL": api.url})
        finally:
            api.close()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(preds), 60)
        self.assertIn("BadRequestError 400", r.stderr)
        self.assertNotIn("cannot parse", r.stderr)
        self.assertNotIn("falciparum", r.stderr)


if __name__ == "__main__":
    unittest.main()
