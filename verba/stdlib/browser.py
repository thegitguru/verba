from __future__ import annotations
"""
Puppeteer-like browser automation for Verba.
Requires:  pip install playwright && python -m playwright install chromium
"""
from typing import Any


def _get_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        raise RuntimeError(
            "The browser module requires Playwright. "
            "Install it with: pip install playwright && python -m playwright install chromium"
        )


# Module-level browser/page state (one browser per Verba process)
_state: dict[str, Any] = {"pw": None, "browser": None, "page": None}


def browser_open(url: str, headless: str = "true") -> str:
    sync_playwright = _get_playwright()
    if _state["pw"] is None:
        _state["pw"] = sync_playwright().start()
        _state["browser"] = _state["pw"].chromium.launch(headless=(headless.lower() != "false"))
        _state["page"] = _state["browser"].new_page()
    _state["page"].goto(url)
    return _state["page"].title()


def browser_goto(url: str) -> str:
    _require_page()
    _state["page"].goto(url)
    return _state["page"].title()


def browser_click(selector: str) -> str:
    _require_page()
    _state["page"].click(selector)
    return "clicked"


def browser_type(selector: str, text: str) -> str:
    _require_page()
    _state["page"].fill(selector, text)
    return "typed"


def browser_read(selector: str) -> str:
    _require_page()
    el = _state["page"].query_selector(selector)
    if el is None:
        return ""
    return el.inner_text()


def browser_read_html(selector: str) -> str:
    _require_page()
    el = _state["page"].query_selector(selector)
    if el is None:
        return ""
    return el.inner_html()


def browser_screenshot(path: str) -> str:
    _require_page()
    _state["page"].screenshot(path=path)
    return path


def browser_wait(ms: str) -> str:
    _require_page()
    _state["page"].wait_for_timeout(int(float(ms)))
    return "waited"


def browser_wait_for(selector: str) -> str:
    _require_page()
    _state["page"].wait_for_selector(selector)
    return "ready"


def browser_title() -> str:
    _require_page()
    return _state["page"].title()


def browser_url() -> str:
    _require_page()
    return _state["page"].url


def browser_eval(js: str) -> str:
    _require_page()
    result = _state["page"].evaluate(js)
    return str(result) if result is not None else ""


def browser_close() -> str:
    if _state["browser"]:
        _state["browser"].close()
    if _state["pw"]:
        _state["pw"].stop()
    _state.update({"pw": None, "browser": None, "page": None})
    return "closed"


def _require_page():
    if _state["page"] is None:
        raise RuntimeError("No browser open. Call browser.open first.")


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
