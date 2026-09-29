"""Web UI for the dashboard agent — split layout: chat on the left, live dashboard on the right.

Reuses the 5 tools and Responses API loop from app.py. Zero extra dependencies
(stdlib http.server); openai / pandas / matplotlib are already required by app.py.

Run:  python server.py   ->  open http://localhost:8000
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import app  # client, MODEL, TOOLS, TOOL_FNS, SYSTEM

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 8077))

# Single in-memory conversation for the demo (one browser session).
SESSION = {"input": [{"role": "system", "content": app.SYSTEM}]}


def _table_from(name: str, output: dict) -> dict | None:
    """Turn a tool result into a table artifact when it carries tabular rows."""
    rows = output.get("rows")
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return {"type": "table", "title": name, "columns": list(rows[0].keys()), "rows": rows}
    return None


def run_turn(question: str) -> dict:
    """Run one agent turn; return the reply text plus any chart/table artifacts produced."""
    SESSION["input"].append({"role": "user", "content": question})
    artifacts, tool_trace = [], []

    for _ in range(8):
        resp = app.client.responses.create(model=app.MODEL, input=SESSION["input"], tools=app.TOOLS)
        SESSION["input"] += resp.output
        calls = [item for item in resp.output if item.type == "function_call"]
        if not calls:
            return {"reply": resp.output_text, "artifacts": artifacts, "tools": tool_trace}

        for call in calls:
            args = json.loads(call.arguments)
            try:
                output = app.TOOL_FNS[call.name](**args)
            except Exception as e:
                output = {"error": f"{type(e).__name__}: {e}"}
            tool_trace.append({"name": call.name, "args": args})

            if isinstance(output, dict) and output.get("chart_path"):
                artifacts.append({"type": "chart", "title": args.get("title") or call.name,
                                  "url": "/" + os.path.relpath(output["chart_path"], HERE).replace(os.sep, "/")})
            elif isinstance(output, dict):
                table = _table_from(call.name, output)
                if table:
                    artifacts.append(table)

            SESSION["input"].append(
                {"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(output)}
            )
    return {"reply": "Stopped: reached max turns.", "artifacts": artifacts, "tools": tool_trace}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if re.fullmatch(r"/charts/[\w.\-]+\.png", path):
            fp = os.path.join(HERE, path.lstrip("/"))
            if os.path.exists(fp):
                with open(fp, "rb") as f:
                    return self._send(200, f.read(), "image/png")
        self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path != "/chat":
            return self._send(404, b'{"error":"not found"}')
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or "{}")
        if body.get("reset"):
            SESSION["input"] = [{"role": "system", "content": app.SYSTEM}]
            return self._send(200, b'{"reply":"Conversation reset.","artifacts":[],"tools":[]}')
        try:
            result = run_turn(body.get("message", ""))
        except Exception as e:
            result = {"reply": f"Server error: {type(e).__name__}: {e}", "artifacts": [], "tools": []}
        self._send(200, json.dumps(result).encode())

    def log_message(self, *args):
        pass  # quiet


if __name__ == "__main__":
    print(f"Dashboard agent UI  ->  http://localhost:{PORT}")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
