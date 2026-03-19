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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="verba", description="Run Verba (natural English) programs.")
    p.add_argument("file", nargs="?", help="Path to a .vrb (Verba) file.")
    p.add_argument("--repl", action="store_true", help="Start an interactive REPL.")

    ns = p.parse_args(argv)

    try:
        if ns.repl or ns.file is None:
            return repl()
        return run_file(Path(ns.file))
    except (VerbaParseError, VerbaRuntimeError) as e:
        print(e, file=sys.stderr)
        return 1
    except VerbaError as e:
        print(e, file=sys.stderr)
        return 1
