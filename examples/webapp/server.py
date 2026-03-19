"""
Thin HTTP runner. All application logic lives in Verba (.vrb) scripts.
This file only handles socket I/O and calls `python -m verba <script>`.
"""
import http.server, subprocess, sys, json, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent
VERBA = [sys.executable, "-m", "verba"]


def run_vrb(script: str, stdin: str = "") -> str:
    result = subprocess.run(
        VERBA + [str(BASE / script)],
        input=stdin, capture_output=True, text=True, cwd=str(BASE)
    )
    return (result.stdout + result.stderr).strip()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_): pass  # silence default logging

    def _send(self, body: str, mime="text/html"):
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/" or path == "/index.html":
            self._send((BASE / "index.html").read_text())
        elif path == "/todos":
            self._send(run_vrb("list_todos.vrb"), "text/plain")
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(body)

        path = urllib.parse.urlparse(self.path).path

        if path == "/calc":
            a = params.get("a", ["0"])[0]
            b = params.get("b", ["0"])[0]
            op = params.get("op", ["+"])[0]
            out = run_vrb("calc.vrb", stdin=f"{a}\n{b}\n{op}\n")
            self._send(out, "text/plain")

        elif path == "/add_todo":
            item = params.get("item", [""])[0]
            out = run_vrb("add_todo.vrb", stdin=f"{item}\n")
            self._send(out, "text/plain")

        elif path == "/clear_todos":
            out = run_vrb("clear_todos.vrb")
            self._send(out, "text/plain")

        else:
            self.send_error(404)


if __name__ == "__main__":
    port = 5000
    print(f"Verba Web App running at http://localhost:{port}")
    print("All logic is in .vrb files — server.py is just the HTTP runner.")
    http.server.HTTPServer(("", port), Handler).serve_forever()
