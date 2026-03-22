from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import VerbaError, VerbaParseError, VerbaRuntimeError
from .parser import parse
from .runtime import Interpreter
from . import pkg

import time
import os


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


def watch_file(path: Path) -> int:
    if not path.exists():
        print(f"I cannot watch '{path}' because it does not exist.")
        return 1
    
    print(f"👀 Watching '{path}' for changes... (Press Ctrl+C to stop)")
    last_mtime = path.stat().st_mtime
    
    # Initial run
    print("-" * 30)
    try:
        run_file(path)
    except Exception as e:
        print(f"Error during execution: {e}")
    print("-" * 30)

    try:
        while True:
            time.sleep(0.5)
            if not path.exists(): continue
            
            current_mtime = path.stat().st_mtime
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                # Clear terminal screen for a fresh look on each reload
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"🔄 Change detected in '{path}'! Re-running...\n")
                print("-" * 30)
                try:
                    run_file(path)
                except Exception as e:
                    print(f"Error during execution: {e}")
                print("-" * 30)
                print("\nWaiting for next change...")
    except KeyboardInterrupt:
        print("\nStopped watching.")
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


VERSION = "1.6.0"

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="verba", description="Run Verba (natural English) programs.")
    sub = p.add_subparsers(dest="command")
    
    # run (default)
    run_p = sub.add_parser("run", help="Run a Verba script.")
    run_p.add_argument("file", help="The .vrb file to run.")
    
    # check
    check_p = sub.add_parser("check", help="Parse script without running.")
    check_p.add_argument("file")
    
    # repl
    sub.add_parser("repl", help="Start interactive shell.")
    
    # install
    inst_p = sub.add_parser("install", help="Install a package from the registry or a URL. If no arguments are provided, installs dependencies listed in verba.json.")
    inst_p.add_argument("package", nargs="?", help="Name of the package, or a direct URL to a .vrb file.")

    # format
    fmt_p = sub.add_parser("format", help="Format a Verba script.")
    fmt_p.add_argument("file")

    # init
    init_p = sub.add_parser("init", help="Initialize a new Verba project.")
    init_p.add_argument("name", help="Name of the project directory.")

    # remove
    rm_p = sub.add_parser("remove", help="Remove an installed package.")
    rm_p.add_argument("package", help="Name of the package to remove.")

    # update
    up_p = sub.add_parser("update", help="Update a specific package, or all packages in verba.json.")
    up_p.add_argument("package", nargs="?", help="Name of the package to update.")
    
    # search
    search_p = sub.add_parser("search", help="Search for a package in the registry.")
    search_p.add_argument("query", help="Search query (package name).")

    # list
    sub.add_parser("list", help="List currently installed packages.")

    # watch
    watch_p = sub.add_parser("watch", help="Watch a Verba script and re-run on changes.")
    watch_p.add_argument("file", help="The .vrb file to watch.")

    # outdated
    sub.add_parser("outdated", help="List packages that have updates available.")

    # sync
    sub.add_parser("sync", help="Synchronize modules with the verba-lock.json file.")

    # original/legacy args (for backward compatibility if possible)
    p.add_argument("legacy_file", nargs="?", help="Legacy file argument.")
    p.add_argument("--repl",    action="store_true", help="Start an interactive REPL.")
    p.add_argument("-v", "--version", action="store_true", help="Print version and exit.")
    p.add_argument("--check",   action="store_true", help="Parse only — do not run.")

    ns = p.parse_args(argv)

    if ns.version:
        print(f"verba {VERSION}")
        return 0

    try:
        # Check subcommands
        if ns.command == "install":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.install(ns.package)
        if ns.command == "format":
            return format_file(Path(ns.file))
        if ns.command == "check":
            return check_file(Path(ns.file))
        if ns.command == "repl":
            return repl()
        if ns.command == "remove":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.remove(ns.package)
        if ns.command == "update":
            try: from . import pkg
            except ImportError: import pkg
            # treat 'all' as None to trigger full update
            pkg_name = None if ns.package == "all" else ns.package
            return pkg.update(pkg_name)
        if ns.command == "outdated":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.list_pkgs(outdated_only=True)
        if ns.command == "sync":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.install(sync_only=True)
        if ns.command == "init":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.init(ns.name)
        if ns.command == "list":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.list_pkgs()
        if ns.command == "search":
            try: from . import pkg
            except ImportError: import pkg
            return pkg.search(ns.query)
        if ns.command == "run":
            return run_file(Path(ns.file))
        if ns.command == "watch":
            return watch_file(Path(ns.file))
            
        # legacy handling
        if ns.repl or (ns.command is None and ns.legacy_file is None):
            return repl()
        if ns.check:
             return check_file(Path(ns.legacy_file))
        if ns.legacy_file:
             return run_file(Path(ns.legacy_file))
        
        return repl()
    except (VerbaParseError, VerbaRuntimeError) as e:
        import traceback
        traceback.print_exc()
        print(e, file=sys.stderr)
        return 1
    except VerbaError as e:
        print(e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
