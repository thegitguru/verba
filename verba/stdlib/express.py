from __future__ import annotations
"""
Express-like router/server module for Verba.
Works alongside the built-in `serve on port` but adds:
  - app.use  (global middleware / static file serving)
  - app.get / app.post / app.put / app.delete  (method-scoped route registration)
  - app.listen  (start server, blocking)
  - json_stringify / json_parse  (JSON helpers)
  - send_json helper  (sets Content-Type automatically)
"""
import http.server
import json as _json
import mimetypes
import os
import threading
import urllib.parse
from pathlib import Path
from typing import Any, Callable


# ── shared app state ──────────────────────────────────────────────────────────

class _App:
    def __init__(self):
        self.routes:     list[tuple[str, str, Callable]] = []   # (method, path, handler)
        self.middleware: list[Callable] = []
        self.static_dir: str | None = None
        self.static_prefix: str = "/static"

_APP = _App()


# ── route registration ────────────────────────────────────────────────────────

def express_get(path: str, handler_name: str) -> str:
    _APP.routes.append(("GET", path, handler_name))
    return f"GET {path} registered"

def express_post(path: str, handler_name: str) -> str:
    _APP.routes.append(("POST", path, handler_name))
    return f"POST {path} registered"

def express_put(path: str, handler_name: str) -> str:
    _APP.routes.append(("PUT", path, handler_name))
    return f"PUT {path} registered"

def express_delete(path: str, handler_name: str) -> str:
    _APP.routes.append(("DELETE", path, handler_name))
    return f"DELETE {path} registered"

def express_use(path_or_dir: str, prefix: str = "/static") -> str:
    """Mount a static directory.  express_use('/public', '/static')"""
    _APP.static_dir = path_or_dir
    _APP.static_prefix = prefix
    return f"static {path_or_dir} at {prefix}"


# ── JSON helpers ──────────────────────────────────────────────────────────────

def json_stringify(value: str) -> str:
    """Wrap a Verba string value in a JSON string (escapes quotes etc.)."""
    return _json.dumps(value)

def json_parse_key(json_str: str, key: str) -> str:
    """Extract a top-level key from a JSON string."""
    try:
        d = _json.loads(json_str)
        v = d.get(key, "")
        return str(v) if not isinstance(v, str) else v
    except Exception:
        return ""

def json_build(*pairs: str) -> str:
    """Build a JSON object from alternating key, value strings."""
    d = {}
    it = iter(pairs)
    for k in it:
        v = next(it, "")
        d[k] = v
    return _json.dumps(d)

def json_array_length(json_str: str) -> str:
    try:
        return str(len(_json.loads(json_str)))
    except Exception:
        return "0"

def json_array_item(json_str: str, index: str) -> str:
    try:
        arr = _json.loads(json_str)
        item = arr[int(index)]
        return item if isinstance(item, str) else _json.dumps(item)
    except Exception:
        return ""


# ── server ────────────────────────────────────────────────────────────────────

def express_listen(port: str, interp_ref: Any) -> str:
    """
    Start the express-style HTTP server.
    interp_ref is the Verba Interpreter instance — routes call back into it.
    """
    port_int = int(float(port))
    app = _APP

    class _Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def _dispatch(self, method: str):
            parsed   = urllib.parse.urlparse(self.path)
            path     = parsed.path
            qs       = urllib.parse.parse_qs(parsed.query)
            length   = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8", errors="replace") if length else ""
            form     = urllib.parse.parse_qs(raw_body)

            # Static file serving
            if app.static_dir and path.startswith(app.static_prefix):
                rel = path[len(app.static_prefix):].lstrip("/")
                full = Path(app.static_dir) / rel
                if full.is_file():
                    mime, _ = mimetypes.guess_type(str(full))
                    data = full.read_bytes()
                    self._raw(200, mime or "application/octet-stream", data)
                    return
                self._raw(404, "text/plain", b"Not Found")
                return

            # Route matching (first match wins, supports * wildcard)
            for r_method, r_path, handler_name in app.routes:
                if r_method != method and r_method != "*":
                    continue
                params = _match_path(r_path, path)
                if params is None:
                    continue

                # Build request dict exposed to Verba as request.xxx
                req_props = {
                    "method": method,
                    "path":   path,
                    "body":   raw_body,
                }
                for k, v in qs.items():
                    req_props[f"query_{k}"] = v[0] if v else ""
                for k, v in form.items():
                    req_props[f"form_{k}"] = v[0] if v else ""
                for k, v in params.items():
                    req_props[f"param_{k}"] = v

                from verba.runtime import _VerbaRequest, Environment, _RespondSignal, _RedirectSignal
                req_obj = _VerbaRequest(method, path, qs, form, raw_body, dict(self.headers))
                req_obj.props.update(req_props)

                handler_env = Environment(parent=interp_ref.globals)
                handler_env.set("request", req_obj)

                try:
                    interp_ref._call(handler_name, [], caller_env=handler_env, line_no=0)
                except _RespondSignal as r:
                    self._raw(r.status, r.mime, r.body.encode("utf-8"))
                    return
                except _RedirectSignal as r:
                    self.send_response(r.status)
                    self.send_header("Location", r.url)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                except Exception as e:
                    self._raw(500, "text/plain", str(e).encode())
                    return
                self._raw(200, "text/html", b"")
                return

            self._raw(404, "text/plain", b"404 Not Found")

        def _raw(self, status: int, mime: str, data: bytes):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", len(data))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):    self._dispatch("GET")
        def do_POST(self):   self._dispatch("POST")
        def do_PUT(self):    self._dispatch("PUT")
        def do_DELETE(self): self._dispatch("DELETE")

    server = http.server.HTTPServer(("", port_int), _Handler)
    print(f"Express server listening on http://localhost:{port_int}")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()
    return "stopped"


def _match_path(pattern: str, path: str) -> dict | None:
    """
    Match /users/:id style patterns.
    Returns dict of captured params, or None if no match.
    """
    if pattern == "*":
        return {}
    p_parts = pattern.split("/")
    r_parts = path.split("/")
    if len(p_parts) != len(r_parts):
        return None
    params = {}
    for pp, rp in zip(p_parts, r_parts):
        if pp.startswith(":"):
            params[pp[1:]] = rp
        elif pp != rp:
            return None
    return params


# ── registry ──────────────────────────────────────────────────────────────────

FUNCTIONS: dict[str, tuple] = {
    "get":          (express_get,        ["path", "handler"]),
    "post":         (express_post,       ["path", "handler"]),
    "put":          (express_put,        ["path", "handler"]),
    "delete":       (express_delete,     ["path", "handler"]),
    "use":          (express_use,        ["dir", "prefix"]),
    "listen":       (express_listen,     ["port", "__interp__"]),
    "json_str":     (json_stringify,     ["value"]),
    "json_key":     (json_parse_key,     ["json", "key"]),
    "json_build":   (json_build,         ["pairs"]),
    "json_arr_len": (json_array_length,  ["json"]),
    "json_arr_item":(json_array_item,    ["json", "index"]),
}

# Special marker so the runtime knows to inject the interpreter reference
NEEDS_INTERP = {"listen"}
