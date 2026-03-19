from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import VerbaError, VerbaParseError, VerbaRuntimeError
from .parser import parse
from .runtime import Interpreter


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def run_file(path: Path) -> int:
    source = _read_text(path)
    program = parse(source)
    Interpreter().run(program)
    return 0


def check_file(path: Path) -> int:
    source = _read_text(path)
    parse(source)
    print(f"OK: {path}")
    return 0


def repl() -> int:
    print("Verba REPL. Type 'end.' on its own line to exit.")
    try:
        import readline  # noqa: F401 — enables arrow-key history on Unix/Windows
    except ImportError:
        pass
    interp = Interpreter()
    buf: list[str] = []
    while True:
        try:
            line = input("verba ")
        except EOFError:
            print()
            break
        if line.strip().lower() == "end.":
            break
        buf.append(line)
        # Try to parse the whole buffer so blocks can be typed across multiple lines.
        try:
            program = parse("\n".join(buf))
        except VerbaParseError as e:
            # Keep buffering only if it's an unfinished block.
            if str(e).startswith("I expected 'end"):
                continue
            print(e, file=sys.stderr)
            buf = []
            continue
        try:
            interp.run(program)
        except VerbaError as e:
            print(e, file=sys.stderr)
        buf = []
    return 0


def install_pkg(url: str) -> int:
    import urllib.request
    from urllib.parse import urlparse
    from .pkg_registry import record_install, MODULES_DIR

    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        print(f"Error: Could not determine package name for URL: {url}")
        return 1
    if not name.endswith(".vrb"):
        name += ".vrb"

    print(f"Installing {name} from {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
        MODULES_DIR.mkdir(exist_ok=True)
        (MODULES_DIR / name).write_bytes(content)
        record_install(name, url)
        print(f"Verbix: installed {name} -> {MODULES_DIR / name}")
        return 0
    except Exception as e:
        print(f"Verbix: failed to install package: {e}")
        return 1


def uninstall_pkg(name: str) -> int:
    from .pkg_registry import record_uninstall, MODULES_DIR

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
    from .pkg_registry import list_packages

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
    from .pkg_registry import get_package, MODULES_DIR

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


def _verbix_main(args: list[str]) -> int:
    """Handles: verba verbix <install|uninstall|packages|info> [arg]"""
    usage = (
        "Verbix — Verba Package Manager\n"
        "  verba verbix install <name>/<url> Install a package\n"
        "  verba verbix uninstall <name>     Uninstall a package\n"
        "  verba verbix packages             List installed packages\n"
        "  verba verbix info <name>          Show package info\n"
    )
    if not args:
        print(usage)
        return 0
    cmd, *rest = args
    if cmd == "install":
        if not rest:
            print("Verbix: provide a URL.  verba verbix install <url>")
            return 1
        return install_pkg(rest[0])
    if cmd == "uninstall":
        if not rest:
            print("Verbix: provide a package name.  verba verbix uninstall <name>")
            return 1
        return uninstall_pkg(rest[0])
    if cmd == "packages":
        return list_pkgs()
    if cmd == "info":
        if not rest:
            print("Verbix: provide a package name.  verba verbix info <name>")
            return 1
        return pkg_info(rest[0])
    print(f"Verbix: unknown command '{cmd}'.\n")
    print(usage)
    return 1


def format_file(path: Path) -> int:
    try:
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
        indent = 0
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                new_lines.append("")
                continue
            
            ls = stripped.lower()
            # words that decrease indent for the current line
            if ls.startswith("end.") or ls.startswith("else:") or ls.startswith("otherwise:") or ls.startswith("on error") or ls.startswith("finally:"):
                indent = max(0, indent - 4)
            
            new_lines.append(" " * indent + stripped)
            
            # words that increase indent for the NEXT lines
            if stripped.endswith(":") or ls.endswith("as follows:"):
                indent += 4
        
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"Formatted {path}")
        return 0
    except Exception as e:
        print(f"I failed to format the file: {e}")
        return 1


def main(argv: list[str] | None = None) -> int:
    raw = argv if argv is not None else sys.argv[1:]

    # Legacy flag handling (before argparse sees subcommands)
    if not raw:
        return repl()
    if raw == ["--version"]:
        print("verba 0.1.0")
        return 0
    if raw == ["--repl"]:
        return repl()
    if len(raw) == 2 and raw[0] == "--check":
        try:
            return check_file(Path(raw[1]))
        except (VerbaParseError, VerbaRuntimeError) as e:
            print(e, file=sys.stderr)
            return 1
    if len(raw) == 1 and raw[0].endswith(".vrb"):
        try:
            return run_file(Path(raw[0]))
        except (VerbaParseError, VerbaRuntimeError) as e:
            print(e, file=sys.stderr)
            return 1

    # "verba verbix <cmd> [args]" — Verbix package manager namespace
    if raw and raw[0] == "verbix":
        return _verbix_main(raw[1:])

    p = argparse.ArgumentParser(prog="verba", description="Run Verba programs.")
    sub = p.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a Verba script.")
    run_p.add_argument("file")

    check_p = sub.add_parser("check", help="Parse without running.")
    check_p.add_argument("file")

    sub.add_parser("repl", help="Start interactive shell.")

    inst_p = sub.add_parser("install", help="Install a package from a URL.")
    inst_p.add_argument("url")

    uninst_p = sub.add_parser("uninstall", help="Uninstall a package by name.")
    uninst_p.add_argument("name")

    sub.add_parser("packages", help="List installed packages.")

    info_p = sub.add_parser("pkg-info", help="Show info about an installed package.")
    info_p.add_argument("name")

    fmt_p = sub.add_parser("format", help="Format a Verba script.")
    fmt_p.add_argument("file")

    ns = p.parse_args(raw)

    try:
        if ns.command == "run":       return run_file(Path(ns.file))
        if ns.command == "check":     return check_file(Path(ns.file))
        if ns.command == "repl":      return repl()
        if ns.command == "install":   return install_pkg(ns.url)
        if ns.command == "uninstall": return uninstall_pkg(ns.name)
        if ns.command == "packages":  return list_pkgs()
        if ns.command == "pkg-info":  return pkg_info(ns.name)
        if ns.command == "format":    return format_file(Path(ns.file))
        return repl()
    except (VerbaParseError, VerbaRuntimeError) as e:
        print(e, file=sys.stderr)
        return 1
    except VerbaError as e:
        print(e, file=sys.stderr)
        return 1
