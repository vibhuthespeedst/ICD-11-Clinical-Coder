import json
import os
import sys
import threading

import anthropic

from .jsonish import INSTRUCTION, parse_json

PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}
FALLBACK_MODELS = ["claude-haiku-5-5", "claude-haiku-4-5", "claude-sonnet-5-5"]


class AnthropicLLM:
    name = "anthropic"

    def __init__(self):
        first = os.environ.get("CODER_ANTHROPIC_MODEL") or FALLBACK_MODELS[0]
        self.models = [first] + [m for m in FALLBACK_MODELS if m != first]
        self.model = self.models[0]
        self.effort = os.environ.get("CODER_EFFORT", "medium")
        self.client = anthropic.Anthropic(max_retries=3, timeout=90.0)
        self.lock = threading.Lock()
        self.mode = 0

    def _next_model(self, failed):
        with self.lock:
            if self.model != failed:
                return True
            i = self.models.index(failed) + 1
            if i >= len(self.models):
                return False
            self.model = self.models[i]
            print(f"anthropic: {failed} unavailable, trying {self.model}", file=sys.stderr)
            return True

    def _create(self, model, system, user, schema, mode):
        kwargs = {}
        output_config = {}
        if mode == 0:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        else:
            system += INSTRUCTION + json.dumps(schema)
        if mode < 2 and not model.startswith("claude-haiku-4"):
            output_config["effort"] = self.effort
        if output_config:
            kwargs["output_config"] = output_config
        return self.client.messages.create(
            model=model,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": user}],
            **kwargs,
        )

    def complete(self, system, user, schema):
        while True:
            model, mode = self.model, self.mode
            try:
                resp = self._create(model, system, user, schema, mode)
                break
            except anthropic.NotFoundError:
                if not self._next_model(model):
                    raise
            except anthropic.BadRequestError:
                if mode >= 2:
                    raise
                with self.lock:
                    if self.mode == mode:
                        self.mode = mode + 1
                        print(f"anthropic: request rejected, retrying with output mode {self.mode}", file=sys.stderr)
        pin, pout = PRICES.get(model, (4.00, 20.00))
        cost = (resp.usage.input_tokens * pin + resp.usage.output_tokens * pout) / 1e6
        if resp.stop_reason != "end_turn":
            return None, cost
        text = next((b.text for b in resp.content if b.type == "text"), None)
        return (parse_json(text) if text else None), cost

    @staticmethod
    def is_fatal(err):
        return isinstance(err, (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError))

    @staticmethod
    def is_transient(err):
        return isinstance(err, anthropic.RateLimitError) or (isinstance(err, anthropic.APIStatusError) and err.status_code >= 500)

