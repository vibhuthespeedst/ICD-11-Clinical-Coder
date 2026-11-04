import json
import os
import re

import openai

PREFERRED = ["gpt-5.1-mini", "gpt-5-mini", "gpt-4.1-mini", "gpt-4o-mini"]
PRICE = (0.25, 2.00)
MODES = ["json_schema", "json_object", "text"]


def _version(model_id):
    return tuple(int(x) for x in re.findall(r"\d+", model_id))


class OpenAILLM:
    name = "openai"

    def __init__(self):
        self.client = openai.OpenAI(max_retries=3, timeout=90.0)
        self.model = os.environ.get("CODER_OPENAI_MODEL") or self._pick_model()
        self.mode = 0

    def _pick_model(self):
        try:
            available = {m.id for m in self.client.models.list()}
        except Exception:
            return PREFERRED[0]
        for m in PREFERRED:
            if m in available:
                return m
        minis = [m for m in available if re.fullmatch(r"gpt-[0-9.]+-mini", m)]
        return max(minis, key=_version) if minis else PREFERRED[0]

    def _create(self, system, user, schema, mode):
        kwargs = {}
        if MODES[mode] == "json_schema":
            kwargs["response_format"] = {"type": "json_schema", "json_schema": {"name": "result", "schema": schema, "strict": True}}
        else:
            system += "\n\nReply with only one JSON object that matches this JSON Schema:\n" + json.dumps(schema)
            if MODES[mode] == "json_object":
                kwargs["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_completion_tokens=8000,
            **kwargs,
        )

    def complete(self, system, user, schema):
        while True:
            mode = self.mode
            try:
                resp = self._create(system, user, schema, mode)
                break
            except openai.BadRequestError:
                if mode + 1 >= len(MODES):
                    raise
                self.mode = max(self.mode, mode + 1)
        u = resp.usage
        cost = ((u.prompt_tokens if u else 0) * PRICE[0] + (u.completion_tokens if u else 0) * PRICE[1]) / 1e6
        choice = resp.choices[0]
        if choice.finish_reason != "stop" or not choice.message.content:
            return None, cost
        text = choice.message.content.strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        return json.loads(text), cost

    @staticmethod
    def is_fatal(err):
        return isinstance(err, (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError))

    @staticmethod
    def is_transient(err):
        return isinstance(err, openai.RateLimitError) or (isinstance(err, openai.APIStatusError) and err.status_code >= 500)
