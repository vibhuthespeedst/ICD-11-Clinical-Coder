import json
import os

import anthropic

PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}


class AnthropicLLM:
    name = "anthropic"

    def __init__(self):
        self.model = os.environ.get("CODER_ANTHROPIC_MODEL", "claude-haiku-5-5")
        self.effort = os.environ.get("CODER_EFFORT", "medium")
        self.client = anthropic.Anthropic(max_retries=3, timeout=90.0)

    def complete(self, system, user, schema):
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
        )
        pin, pout = PRICES.get(self.model, (4.00, 20.00))
        cost = (resp.usage.input_tokens * pin + resp.usage.output_tokens * pout) / 1e6
        if resp.stop_reason != "end_turn":
            return None, cost
        text = next((b.text for b in resp.content if b.type == "text"), None)
        return (json.loads(text) if text else None), cost

    @staticmethod
    def is_fatal(err):
        return isinstance(err, (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError))
