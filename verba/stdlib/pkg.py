"""verbix — Verbix package manager stdlib module for Verba.

Available in every script as `verbix`:
    verbix.install with name_or_url
    verbix.uninstall with name
    verbix.list
    verbix.info with name
    verbix.installed with name
    verbix.search with query
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from verba.pkg_registry import (
    record_install,
    record_uninstall,
    list_packages,
    get_package,
    MODULES_DIR,
)


def _resolve(name_or_url: str) -> tuple[str, str, str]:
    from verba.verbix_cli import _resolve as cli_resolve
    return cli_resolve(name_or_url)


def _install(name_or_url: str) -> str:
    try:
        url, pkg_name, version = _resolve(name_or_url)
    except RuntimeError as e:
        return str(e)
    MODULES_DIR.mkdir(exist_ok=True)
    with urllib.request.urlopen(url) as r:
        content = r.read()
    (MODULES_DIR / pkg_name).write_bytes(content)
    record_install(pkg_name, url, version)
    return f"Installed {pkg_name} v{version}"


def _uninstall(name: str) -> str:
    if not name.endswith(".vrb"):
        name += ".vrb"
    path = MODULES_DIR / name
    removed_file = False
    if path.exists():
        path.unlink()
        removed_file = True
    removed_reg = record_uninstall(name)
    if removed_file or removed_reg:
        return f"Uninstalled {name}"
    return f"Package {name} was not installed"


def _list() -> str:
    pkgs = list_packages()
    if not pkgs:
        return "No packages installed."
    lines = [f"{n}  ({v['version']})  {v['url']}" for n, v in pkgs.items()]
    return "\n".join(lines)


def _info(name: str) -> str:
    if not name.endswith(".vrb"):
        name += ".vrb"
    pkg = get_package(name)
    if pkg is None:
        return f"Package {name} is not installed."
    return f"name: {name}\nversion: {pkg['version']}\nurl: {pkg['url']}"


def _installed(name: str) -> str:
    if not name.endswith(".vrb"):
        name += ".vrb"
    return "true" if get_package(name) is not None else "false"


def _search(query: str) -> str:
    from verba.verbix_cli import _fetch_index
    try:
        index = _fetch_index()
    except RuntimeError as e:
        return str(e)
    q = query.lower()
    results = {k: v for k, v in index.items() if q in k or q in v.get("description", "").lower()}
    if not results:
        return f"No packages found matching '{query}'."
    lines = [f"{k}  v{v.get('version','?')}  {v.get('description','')}" for k, v in results.items()]
    return "\n".join(lines)


FUNCTIONS: dict = {
    "install":   (_install,   ["name_or_url"]),
    "uninstall": (_uninstall, ["name"]),
    "list":      (_list,      []),
    "info":      (_info,      ["name"]),
    "installed": (_installed, ["name"]),
    "search":    (_search,    ["query"]),
}

NEEDS_INTERP: set = set()
