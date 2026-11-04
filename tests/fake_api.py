import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CANDIDATE = re.compile(r"^([0-9A-Z]{4}(?:\.[0-9A-Z]{1,3})?) \| ", re.M)
EXTRACT = {
    "language": "English",
    "diagnoses": [{"term": "malaria", "search_terms": ["malaria"], "details": "none"}],
    "icd10_codes": ["B54"],
    "code_guesses": [],
}


class FakeAPI:
    """Local stand-in for the Anthropic and OpenAI HTTP APIs: answers the extract step with a fixed
    diagnosis and the choose step with the first three candidates it was shown."""

    def __init__(self, fail_first=0):
        self.requests = []
        self.fail_first = fail_first
        self.lock = threading.Lock()
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send(self, status, payload, headers=()):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                for k, v in headers:
                    self.send_header(k, v)
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self.send(200, {"object": "list", "data": [{"id": "gpt-5.1-mini", "object": "model", "created": 0, "owned_by": "fake"}]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["content-length"])))
                with api.lock:
                    api.requests.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body})
                    failing = api.fail_first > 0
                    api.fail_first -= 1
                if failing:
                    self.send(429, {"type": "error", "error": {"type": "rate_limit_error", "message": "slow down"}}, [("retry-after", "0")])
                elif self.path.endswith("/v1/messages"):
                    schema = body["output_config"]["format"]["schema"]
                    out = api.answer(schema, body["messages"][0]["content"])
                    self.send(200, {
                        "id": "msg_fake", "type": "message", "role": "assistant", "model": body["model"],
                        "content": [{"type": "text", "text": json.dumps(out)}],
                        "stop_reason": "end_turn", "stop_sequence": None,
                        "usage": {"input_tokens": 100, "output_tokens": 20},
                    })
                elif self.path.endswith("/chat/completions"):
                    schema = body["response_format"]["json_schema"]["schema"]
                    out = api.answer(schema, body["messages"][-1]["content"])
                    self.send(200, {
                        "id": "chatcmpl-fake", "object": "chat.completion", "created": 0, "model": body["model"],
                        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(out)}}],
                        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
                    })
                else:
                    self.send(404, {"error": {"message": "unknown path"}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @staticmethod
    def answer(schema, user_text):
        if "icd10_codes" in schema["properties"]:
            return EXTRACT
        return {"codes": CANDIDATE.findall(user_text)[:3]}

    def close(self):
        self.server.shutdown()
