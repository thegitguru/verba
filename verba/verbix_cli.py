"""verbix_cli.py — Verbix package manager, runs standalone without verba."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def install_pkg(url: str) -> int:
    import urllib.request
    from urllib.parse import urlparse
    from verba.pkg_registry import record_install, MODULES_DIR

    name = Path(urlparse(url).path).name
    if not name:
        print(f"Verbix: cannot determine package name from URL: {url}")
        return 1
    if not name.endswith(".vrb"):
        name += ".vrb"

    print(f"Verbix: installing {name} from {url}...")
    try:
        with urllib.request.urlopen(url) as r:
            content = r.read()
        MODULES_DIR.mkdir(exist_ok=True)
        (MODULES_DIR / name).write_bytes(content)
        record_install(name, url)
        print(f"Verbix: installed {name} -> {MODULES_DIR / name}")
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


def main(argv: list[str] | None = None) -> int:
    raw = argv if argv is not None else sys.argv[1:]

    if not raw:
        print("Verbix — Verba Package Manager")
        print("  verbix install <url>      Install a package")
        print("  verbix uninstall <name>   Uninstall a package")
        print("  verbix packages           List installed packages")
        print("  verbix info <name>        Show package info")
        print("  verbix --version          Show version")
        return 0

    if raw == ["--version"]:
        print("verbix 1.0.0")
        return 0

    p = argparse.ArgumentParser(
        prog="verbix",
        description="Verbix — Verba Package Manager",
    )
    sub = p.add_subparsers(dest="command")

    inst_p = sub.add_parser("install", help="Install a package from a URL.")
    inst_p.add_argument("url")

    uninst_p = sub.add_parser("uninstall", help="Uninstall a package by name.")
    uninst_p.add_argument("name")

    sub.add_parser("packages", help="List installed packages.")

    info_p = sub.add_parser("info", help="Show info about an installed package.")
    info_p.add_argument("name")

    ns = p.parse_args(raw)

    if ns.command == "install":   return install_pkg(ns.url)
    if ns.command == "uninstall": return uninstall_pkg(ns.name)
    if ns.command == "packages":  return list_pkgs()
    if ns.command == "info":      return pkg_info(ns.name)

    p.print_help()
    return 0
