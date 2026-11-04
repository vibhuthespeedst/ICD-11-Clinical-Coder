import json
import os

import openai

PREFERRED = ["gpt-5.1-mini", "gpt-5-mini", "gpt-4.1-mini", "gpt-4o-mini"]
PRICE = (0.25, 2.00)


class OpenAILLM:
    name = "openai"

    def __init__(self):
        self.client = openai.OpenAI(max_retries=3, timeout=90.0)
        self.model = os.environ.get("CODER_OPENAI_MODEL") or self._pick_model()

    def _pick_model(self):
        try:
            available = {m.id for m in self.client.models.list()}
        except Exception:
            return PREFERRED[0]
        return next((m for m in PREFERRED if m in available), PREFERRED[0])

    def complete(self, system, user, schema):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_schema", "json_schema": {"name": "result", "schema": schema, "strict": True}},
            max_completion_tokens=8000,
        )
        u = resp.usage
        cost = ((u.prompt_tokens if u else 0) * PRICE[0] + (u.completion_tokens if u else 0) * PRICE[1]) / 1e6
        choice = resp.choices[0]
        if choice.finish_reason != "stop" or not choice.message.content:
            return None, cost
        return json.loads(choice.message.content), cost

    @staticmethod
    def is_fatal(err):
        return isinstance(err, (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError))
