from __future__ import annotations
import json as _json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any


def _make_response(status: int, headers: dict, body: str) -> dict:
    """Return a plain dict that Verba Instance.props can be built from."""
    data = None
    try:
        data = _json.loads(body)
    except Exception:
        data = None
    return {
        "status": status,
        "ok": status < 400,
        "body": body,
        "data": _json.dumps(data) if data is not None else body,
        "headers": str(headers),
    }


def _do_request(method: str, url: str, body: str | None, headers: dict) -> dict:
    data = body.encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req) as r:
            return _make_response(r.status, dict(r.headers), r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return _make_response(e.code, dict(e.headers), e.read().decode("utf-8", errors="replace"))
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e


# --- public API called by the runtime ---

def http_get(url: str, headers_json: str = "{}") -> dict:
    h = _json.loads(headers_json) if headers_json else {}
    return _do_request("GET", url, None, h)


def http_post(url: str, body: str = "", headers_json: str = "{}") -> dict:
    h = _json.loads(headers_json) if headers_json else {}
    if not h.get("Content-Type"):
        h["Content-Type"] = "application/x-www-form-urlencoded"
    return _do_request("POST", url, body, h)


def http_post_json(url: str, json_body: str = "{}", headers_json: str = "{}") -> dict:
    h = _json.loads(headers_json) if headers_json else {}
    h["Content-Type"] = "application/json"
    return _do_request("POST", url, json_body, h)


def http_put(url: str, body: str = "", headers_json: str = "{}") -> dict:
    h = _json.loads(headers_json) if headers_json else {}
    return _do_request("PUT", url, body, h)


def http_delete(url: str, headers_json: str = "{}") -> dict:
    h = _json.loads(headers_json) if headers_json else {}
    return _do_request("DELETE", url, None, h)


def http_encode_form(pairs_json: str) -> str:
    """Encode a JSON object as application/x-www-form-urlencoded."""
    d = _json.loads(pairs_json)
    return urllib.parse.urlencode(d)


def http_encode_url(base: str, params_json: str) -> str:
    """Append query params from a JSON object to a base URL."""
    d = _json.loads(params_json)
    return base + "?" + urllib.parse.urlencode(d)


# Registry: name -> (callable, [param_names])
FUNCTIONS: dict[str, tuple] = {
    "get":         (http_get,         ["url", "headers"]),
    "post":        (http_post,        ["url", "body", "headers"]),
    "post_json":   (http_post_json,   ["url", "json", "headers"]),
    "put":         (http_put,         ["url", "body", "headers"]),
    "delete":      (http_delete,      ["url", "headers"]),
    "encode_form": (http_encode_form, ["pairs"]),
    "encode_url":  (http_encode_url,  ["base", "params"]),
}
