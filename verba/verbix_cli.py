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
    url = _registry_url()
    try:
        with urllib.request.urlopen(url) as r:
            return json.loads(r.read().decode())["packages"]
    except Exception as e:
        raise RuntimeError(f"Could not fetch registry from {url}: {e}")


def _parse_name_version(arg: str) -> tuple[str, str | None]:
    """Split 'mathkit@1.0.0' -> ('mathkit', '1.0.0'), 'mathkit' -> ('mathkit', None)."""
    if "@" in arg:
        name, _, ver = arg.partition("@")
        return name.strip(), ver.strip()
    return arg.strip(), None


def _resolve(name_or_url: str) -> tuple[str, str, str]:
    """Return (url, pkg_filename, version)."""
    if name_or_url.startswith("http://") or name_or_url.startswith("https://"):
        url = name_or_url
        pkg_name = Path(urlparse(url).path).name
        if not pkg_name.endswith(".vrb"):
            pkg_name += ".vrb"
        return url, pkg_name, "unknown"

    name, requested_ver = _parse_name_version(name_or_url)
    key = name.lower().removesuffix(".vrb")

    index = _fetch_index()
    if key not in index:
        available = ", ".join(index.keys())
        raise RuntimeError(f"Package '{name}' not found in registry.\nAvailable: {available}")

    entry = index[key]
    latest = entry.get("latest", "unknown")
    versions = entry.get("versions", {})

    # Resolve which version to use
    ver = requested_ver if requested_ver and requested_ver != "latest" else latest

    if ver not in versions:
        available_vers = ", ".join(versions.keys())
        raise RuntimeError(f"Version '{ver}' not found for '{name}'.\nAvailable versions: {available_vers}")

    url = versions[ver]["url"]
    pkg_name = key + ".vrb"
    return url, pkg_name, ver


def _semver_gt(a: str, b: str) -> bool:
    """Return True if version a > version b."""
    try:
        return tuple(int(x) for x in a.split(".")) > tuple(int(x) for x in b.split("."))
    except Exception:
        return a != b


def install_pkg(name_or_url: str) -> int:
    from verba.pkg_registry import record_install, MODULES_DIR

    try:
        url, pkg_name, version = _resolve(name_or_url)
    except RuntimeError as e:
        print(f"Verbix: {e}")
        return 1

    # Check if already installed at same version
    from verba.pkg_registry import get_package
    existing = get_package(pkg_name)
    if existing and existing.get("version") == version:
        print(f"Verbix: {pkg_name} v{version} is already installed.")
        return 0

    print(f"Verbix: installing {pkg_name} v{version} from {url}...")
    try:
        with urllib.request.urlopen(url) as r:
            content = r.read()
        MODULES_DIR.mkdir(exist_ok=True)
        (MODULES_DIR / pkg_name).write_bytes(content)
        record_install(pkg_name, url, version)
        print(f"Verbix: installed {pkg_name} v{version} -> {MODULES_DIR / pkg_name}")
        return 0
    except Exception as e:
        print(f"Verbix: failed to install: {e}")
        return 1


def upgrade_pkg(name: str) -> int:
    """Upgrade a package to its latest version."""
    from verba.pkg_registry import get_package

    key = name.lower().removesuffix(".vrb")
    pkg_name = key + ".vrb"
    existing = get_package(pkg_name)

    try:
        index = _fetch_index()
    except RuntimeError as e:
        print(f"Verbix: {e}")
        return 1

    if key not in index:
        print(f"Verbix: '{name}' not found in registry.")
        return 1

    latest = index[key].get("latest", "unknown")

    if existing and not _semver_gt(latest, existing.get("version", "0.0.0")):
        print(f"Verbix: {pkg_name} is already at latest version ({latest}).")
        return 0

    old_ver = existing.get("version", "none") if existing else "none"
    print(f"Verbix: upgrading {pkg_name} {old_ver} -> {latest}...")
    return install_pkg(f"{key}@{latest}")


def upgrade_all() -> int:
    """Upgrade all installed packages to their latest versions."""
    from verba.pkg_registry import list_packages

    pkgs = list_packages()
    if not pkgs:
        print("Verbix: no packages installed.")
        return 0
    code = 0
    for pkg_name in pkgs:
        code |= upgrade_pkg(pkg_name.removesuffix(".vrb"))
    return code


def outdated_pkgs() -> int:
    """List packages that have a newer version available."""
    from verba.pkg_registry import list_packages

    pkgs = list_packages()
    if not pkgs:
        print("Verbix: no packages installed.")
        return 0

    try:
        index = _fetch_index()
    except RuntimeError as e:
        print(f"Verbix: {e}")
        return 1

    found_outdated = False
    print(f"{'Package':<25} {'Installed':<12} {'Latest':<12} Status")
    print("-" * 65)
    for pkg_name, info in pkgs.items():
        key = pkg_name.removesuffix(".vrb")
        installed_ver = info.get("version", "unknown")
        if key in index:
            latest = index[key].get("latest", "unknown")
            if _semver_gt(latest, installed_ver):
                status = "OUTDATED"
                found_outdated = True
            else:
                status = "up to date"
        else:
            latest = "?"
            status = "not in registry"
        print(f"{pkg_name:<25} {installed_ver:<12} {latest:<12} {status}")

    if not found_outdated:
        print("\nAll packages are up to date.")
    return 0


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

    key = name.lower().removesuffix(".vrb")
    pkg_name = key + ".vrb"
    pkg = get_package(pkg_name)

    # Also show available versions from registry
    try:
        index = _fetch_index()
        reg_entry = index.get(key, {})
        available_versions = list(reg_entry.get("versions", {}).keys())
        latest = reg_entry.get("latest", "?")
    except RuntimeError:
        available_versions = []
        latest = "?"

    if pkg is None:
        print(f"Verbix: package '{pkg_name}' is not installed.")
        if available_versions:
            print(f"Available versions: {', '.join(available_versions)}")
            print(f"Install with: verbix install {key}")
        return 1

    path = MODULES_DIR / pkg_name
    installed_ver = pkg["version"]
    outdated = _semver_gt(latest, installed_ver) if latest != "?" else False

    print(f"Name:      {pkg_name}")
    print(f"Installed: {installed_ver}")
    print(f"Latest:    {latest}{' (upgrade available)' if outdated else ''}")
    print(f"URL:       {pkg['url']}")
    print(f"Path:      {path} ({'exists' if path.exists() else 'missing'})")
    if available_versions:
        print(f"Versions:  {', '.join(available_versions)}")
    return 0


def search_pkgs(query: str) -> int:
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
    print(f"{'Package':<20} {'Latest':<10} Description")
    print("-" * 70)
    for k, v in results.items():
        print(f"{k:<20} {v.get('latest','?'):<10} {v.get('description','')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw = argv if argv is not None else sys.argv[1:]

    if not raw:
        print("Verbix — Verba Package Manager")
        print("  verbix install <name[@ver]>   Install a package (default: latest)")
        print("  verbix uninstall <name>        Uninstall a package")
        print("  verbix upgrade <name>          Upgrade a package to latest")
        print("  verbix upgrade all             Upgrade all installed packages")
        print("  verbix outdated                Show packages with newer versions")
        print("  verbix packages                List installed packages")
        print("  verbix search <query>          Search the registry")
        print("  verbix info <name>             Show package info and versions")
        print("  verbix --version               Show Verbix version")
        return 0

    if raw == ["--version"]:
        print("verbix 1.0.0")
        return 0

    p = argparse.ArgumentParser(prog="verbix", description="Verbix — Verba Package Manager")
    sub = p.add_subparsers(dest="command")

    inst_p = sub.add_parser("install", help="Install a package by name[@version] or URL.")
    inst_p.add_argument("name_or_url")

    uninst_p = sub.add_parser("uninstall", help="Uninstall a package.")
    uninst_p.add_argument("name")

    upg_p = sub.add_parser("upgrade", help="Upgrade a package (or 'all').")
    upg_p.add_argument("name")

    sub.add_parser("outdated", help="Show packages with newer versions available.")
    sub.add_parser("packages", help="List installed packages.")

    info_p = sub.add_parser("info", help="Show package info and available versions.")
    info_p.add_argument("name")

    search_p = sub.add_parser("search", help="Search the registry.")
    search_p.add_argument("query")

    ns = p.parse_args(raw)

    if ns.command == "install":   return install_pkg(ns.name_or_url)
    if ns.command == "uninstall": return uninstall_pkg(ns.name)
    if ns.command == "upgrade":
        return upgrade_all() if ns.name == "all" else upgrade_pkg(ns.name)
    if ns.command == "outdated":  return outdated_pkgs()
    if ns.command == "packages":  return list_pkgs()
    if ns.command == "info":      return pkg_info(ns.name)
    if ns.command == "search":    return search_pkgs(ns.query)

    p.print_help()
    return 0
