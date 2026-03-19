from __future__ import annotations
"""
Browser module for Verba — pure stdlib, no third-party dependencies.
Uses urllib for HTTP fetching and html.parser for basic DOM reading.
"""
import urllib.request
import urllib.parse
import urllib.error
import html.parser
import os
from typing import Any

# ── shared state ──────────────────────────────────────────────────────────────

_state: dict[str, Any] = {
    "url":     "",
    "html":    "",
    "title":   "",
    "headers": {},
}


# ── HTML helpers ──────────────────────────────────────────────────────────────

class _TitleParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


class _SelectorParser(html.parser.HTMLParser):
    """Minimal CSS tag selector — supports 'tag' only (e.g. 'h1', 'p')."""
    def __init__(self, tag: str):
        super().__init__()
        self._target = tag.lower().lstrip("#.")
        self._depth = 0
        self._capture = 0
        self.text = ""
        self.html_inner = ""
        self._raw_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        self._depth += 1
        if tag.lower() == self._target and self._capture == 0:
            self._capture = self._depth

    def handle_endtag(self, tag):
        if self._capture and self._depth == self._capture:
            self._capture = 0
        self._depth -= 1

    def handle_data(self, data):
        if self._capture:
            self.text += data
            self._raw_parts.append(data)


def _parse_title(html_src: str) -> str:
    p = _TitleParser()
    try:
        p.feed(html_src)
    except Exception:
        pass
    return p.title.strip()


def _read_selector(html_src: str, selector: str) -> tuple[str, str]:
    p = _SelectorParser(selector)
    try:
        p.feed(html_src)
    except Exception:
        pass
    return p.text.strip(), "".join(p._raw_parts)


# ── public API ────────────────────────────────────────────────────────────────

def browser_open(url: str, headless: str = "true") -> str:
    """Fetch a URL and store the page. Returns the page title."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Verba/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            _state["html"]    = r.read().decode("utf-8", errors="replace")
            _state["url"]     = url
            _state["headers"] = dict(r.headers)
            _state["title"]   = _parse_title(_state["html"])
    except Exception as e:
        raise RuntimeError(f"browser.open failed: {e}")
    return _state["title"]


def browser_goto(url: str) -> str:
    return browser_open(url)


def browser_read(selector: str) -> str:
    _require_page()
    text, _ = _read_selector(_state["html"], selector)
    return text


def browser_read_html(selector: str) -> str:
    _require_page()
    _, inner = _read_selector(_state["html"], selector)
    return inner


def browser_title() -> str:
    _require_page()
    return _state["title"]


def browser_url() -> str:
    _require_page()
    return _state["url"]


def browser_screenshot(path: str) -> str:
    raise RuntimeError(
        "browser.screenshot requires Playwright. "
        "Install it with: pip install playwright && python -m playwright install chromium"
    )


def browser_click(selector: str) -> str:
    raise RuntimeError(
        "browser.click requires Playwright (a real browser). "
        "Install it with: pip install playwright && python -m playwright install chromium"
    )


def browser_type(selector: str, text: str) -> str:
    raise RuntimeError(
        "browser.type requires Playwright (a real browser). "
        "Install it with: pip install playwright && python -m playwright install chromium"
    )


def browser_wait(ms: str) -> str:
    import time
    time.sleep(float(ms) / 1000)
    return "waited"


def browser_wait_for(selector: str) -> str:
    _require_page()
    text, _ = _read_selector(_state["html"], selector)
    if not text:
        raise RuntimeError(f"Element '{selector}' not found in page.")
    return "ready"


def browser_eval(js: str) -> str:
    raise RuntimeError(
        "browser.eval requires Playwright (a real browser). "
        "Install it with: pip install playwright && python -m playwright install chromium"
    )


def browser_close() -> str:
    _state.update({"url": "", "html": "", "title": "", "headers": {}})
    return "closed"


def _require_page():
    if not _state["html"]:
        raise RuntimeError("No page loaded. Call browser.open first.")


# ── registry ──────────────────────────────────────────────────────────────────

FUNCTIONS: dict[str, tuple] = {
    "open":       (browser_open,       ["url", "headless"]),
    "goto":       (browser_goto,       ["url"]),
    "click":      (browser_click,      ["selector"]),
    "type":       (browser_type,       ["selector", "text"]),
    "read":       (browser_read,       ["selector"]),
    "read_html":  (browser_read_html,  ["selector"]),
    "screenshot": (browser_screenshot, ["path"]),
    "wait":       (browser_wait,       ["ms"]),
    "wait_for":   (browser_wait_for,   ["selector"]),
    "title":      (browser_title,      []),
    "url":        (browser_url,        []),
    "eval":       (browser_eval,       ["js"]),
    "close":      (browser_close,      []),
}
