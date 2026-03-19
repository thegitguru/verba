"""verbix_cli.py — Verbix package manager, runs standalone without verba."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

_CONFIG_FILE = Path(__file__).parent.parent / "verbix.config.json"
_DEFAULT_REGISTRY = "http://localhost:8900/index.json"


def _registry_url() -> str:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8")).get("registry", _DEFAULT_REGISTRY)
        except Exception:
            pass
    return _DEFAULT_REGISTRY


def _fetch_index() -> dict:
    """Fetch the remote index.json and return the packages dict."""
    url = _registry_url()
    try:
        with urllib.request.urlopen(url) as r:
            return json.loads(r.read().decode())["packages"]
    except Exception as e:
        raise RuntimeError(f"Could not fetch registry from {url}: {e}")


def _resolve(name_or_url: str) -> tuple[str, str, str]:
    """
    Given a package name OR a full URL, return (url, pkg_name, version).
    - If it looks like a URL (starts with http), use it directly.
    - Otherwise look it up in the remote index.
    """
    if name_or_url.startswith("http://") or name_or_url.startswith("https://"):
        url = name_or_url
        pkg_name = Path(urlparse(url).path).name
        if not pkg_name.endswith(".vrb"):
            pkg_name += ".vrb"
        return url, pkg_name, "unknown"

    # Name-based lookup
    index = _fetch_index()
    key = name_or_url.lower().removesuffix(".vrb")
    if key not in index:
        available = ", ".join(index.keys())
        raise RuntimeError(f"Package '{name_or_url}' not found in registry.\nAvailable: {available}")
    entry = index[key]
    url = entry["url"]
    pkg_name = key + ".vrb"
    version = entry.get("version", "unknown")
    return url, pkg_name, version


def install_pkg(name_or_url: str) -> int:
    from verba.pkg_registry import record_install, MODULES_DIR

    try:
        url, pkg_name, version = _resolve(name_or_url)
    except RuntimeError as e:
        print(f"Verbix: {e}")
        return 1

    print(f"Verbix: installing {pkg_name} v{version} from {url}...")
    try:
        with urllib.request.urlopen(url) as r:
            content = r.read()
        MODULES_DIR.mkdir(exist_ok=True)
        (MODULES_DIR / pkg_name).write_bytes(content)
        record_install(pkg_name, url, version)
        print(f"Verbix: installed {pkg_name} -> {MODULES_DIR / pkg_name}")
        return 0
    except Exception as e:
        print(f"Verbix: failed to install: {e}")
        return 1


def uninstall_pkg(name: str) -> int:
    from verba.pkg_registry import record_uninstall, MODULES_DIR

    if not name.endswith(".vrb"):
        name += ".vrb"
    path = MODULES_DIR / name
    removed_file = False
    if path.exists():
        path.unlink()
        removed_file = True
    removed_reg = record_uninstall(name)
    if removed_file or removed_reg:
        print(f"Verbix: uninstalled {name}")
        return 0
    print(f"Verbix: package '{name}' is not installed.")
    return 1


def list_pkgs() -> int:
    from verba.pkg_registry import list_packages

    pkgs = list_packages()
    if not pkgs:
        print("Verbix: no packages installed.")
        return 0
    print(f"{'Package':<30} {'Version':<12} URL")
    print("-" * 70)
    for pkg_name, info in pkgs.items():
        print(f"{pkg_name:<30} {info['version']:<12} {info['url']}")
    return 0


def pkg_info(name: str) -> int:
    from verba.pkg_registry import get_package, MODULES_DIR

    if not name.endswith(".vrb"):
        name += ".vrb"
    pkg = get_package(name)
    if pkg is None:
        print(f"Verbix: package '{name}' is not installed.")
        return 1
    path = MODULES_DIR / name
    print(f"Name:    {name}")
    print(f"Version: {pkg['version']}")
    print(f"URL:     {pkg['url']}")
    print(f"Path:    {path} ({'exists' if path.exists() else 'missing'})")
    return 0


def search_pkgs(query: str) -> int:
    """Search the remote registry index by name or description."""
    try:
        index = _fetch_index()
    except RuntimeError as e:
        print(f"Verbix: {e}")
        return 1

    q = query.lower()
    results = {
        k: v for k, v in index.items()
        if q in k.lower() or q in v.get("description", "").lower()
    }
    if not results:
        print(f"Verbix: no packages found matching '{query}'.")
        return 0
    print(f"{'Package':<20} {'Version':<10} Description")
    print("-" * 70)
    for k, v in results.items():
        print(f"{k:<20} {v.get('version','?'):<10} {v.get('description','')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = argv if argv is not None else sys.argv[1:]

    if not raw:
        print("Verbix — Verba Package Manager")
        print("  verbix install <name>/<url> Install a package by name or URL")
        print("  verbix uninstall <name>     Uninstall a package")
        print("  verbix packages             List installed packages")
        print("  verbix search <query>       Search the registry")
        print("  verbix info <name>          Show installed package info")
        print("  verbix --version            Show version")
        return 0

    if raw == ["--version"]:
        print("verbix 1.0.0")
        return 0

    p = argparse.ArgumentParser(prog="verbix", description="Verbix — Verba Package Manager")
    sub = p.add_subparsers(dest="command")

    inst_p = sub.add_parser("install", help="Install a package by name or URL.")
    inst_p.add_argument("name_or_url")

    uninst_p = sub.add_parser("uninstall", help="Uninstall a package by name.")
    uninst_p.add_argument("name")

    sub.add_parser("packages", help="List installed packages.")

    info_p = sub.add_parser("info", help="Show info about an installed package.")
    info_p.add_argument("name")

    search_p = sub.add_parser("search", help="Search the registry.")
    search_p.add_argument("query")

    ns = p.parse_args(raw)

    if ns.command == "install":   return install_pkg(ns.name_or_url)
    if ns.command == "uninstall": return uninstall_pkg(ns.name)
    if ns.command == "packages":  return list_pkgs()
    if ns.command == "info":      return pkg_info(ns.name)
    if ns.command == "search":    return search_pkgs(ns.query)

    p.print_help()
    return 0
