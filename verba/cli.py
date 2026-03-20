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


DEFAULT_REGISTRY_URL = "https://raw.githubusercontent.com/thegitguru/Verba/main/registry.json"

def install_pkg(package: str) -> int:
    import urllib.request
    from urllib.parse import urlparse
    import json
    import os

    is_url = package.startswith("http://") or package.startswith("https://")
    
    if is_url:
        url = package
        parsed = urlparse(url)
        name = Path(parsed.path).name
        if not name:
            print(f"Error: Could not determine package name for URL: {url}")
            return 1
    else:
        registry_url = os.environ.get("VERBA_REGISTRY", DEFAULT_REGISTRY_URL)
        print(f"Fetching registry from {registry_url}...")
        try:
            req = urllib.request.Request(registry_url, headers={'User-Agent': 'Verba'})
            with urllib.request.urlopen(req) as response:
                registry = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"Error fetching registry: {e}")
            return 1
            
        if package not in registry:
            print(f"Error: Package '{package}' not found in registry.")
            return 1
            
        url = registry[package]
        name = package

    if not name.endswith(".vrb"):
        name += ".vrb"
        
    print(f"Installing {name} from {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Verba'})
        with urllib.request.urlopen(req) as response:
            content = response.read()
        
        modules_dir = Path("modules")
        modules_dir.mkdir(exist_ok=True)
        (modules_dir / name).write_bytes(content)
        print(f"Successfully installed package to {modules_dir / name}")
        
        # Update verba.json if it exists
        vjson_path = Path("verba.json")
        if vjson_path.exists():
            try:
                with open(vjson_path, "r", encoding="utf-8") as f:
                    project_data = json.load(f)
                
                if "dependencies" not in project_data:
                    project_data["dependencies"] = {}
                
                pkg_key = name[:-4] if name.endswith(".vrb") else name
                project_data["dependencies"][pkg_key] = url
                
                with open(vjson_path, "w", encoding="utf-8") as f:
                    json.dump(project_data, f, indent=2)
                
                print(f"Updated verba.json with dependency '{pkg_key}'")
            except Exception as e:
                print(f"Warning: Could not update verba.json: {e}")
                
        return 0
    except Exception as e:
        print(f"I failed to install the package: {e}")
        return 1


def remove_pkg(package: str) -> int:
    import json
    
    # Derive name matching what `install_pkg` does
    name = package
    if not name.endswith(".vrb"):
        name += ".vrb"
        
    modules_dir = Path("modules")
    pkg_path = modules_dir / name
    
    if pkg_path.exists():
        try:
            pkg_path.unlink()
            print(f"Removed {pkg_path}")
        except OSError as e:
            print(f"Failed to remove {pkg_path}: {e}")
            return 1
    else:
        print(f"Package '{package}' is not installed in modules/ directory.")
        
    vjson_path = Path("verba.json")
    if vjson_path.exists():
        try:
            with open(vjson_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)
                
            pkg_key = name[:-4]
            if "dependencies" in project_data and pkg_key in project_data["dependencies"]:
                del project_data["dependencies"][pkg_key]
                with open(vjson_path, "w", encoding="utf-8") as f:
                    json.dump(project_data, f, indent=2)
                print(f"Removed dependency '{pkg_key}' from verba.json")
        except Exception as e:
            print(f"Warning: Could not update verba.json: {e}")
            
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


def init_project(name: str) -> int:
    try:
        project_dir = Path(name)
        if project_dir.exists():
            print(f"Error: Directory '{name}' already exists.")
            return 1
            
        project_dir.mkdir(parents=True)
        (project_dir / "main.vrb").write_text("say \"Hello from Verba!\".\n", encoding="utf-8")
        (project_dir / "verba.json").write_text(f'{{\n  "name": "{name}",\n  "version": "1.0.0"\n}}\n', encoding="utf-8")
        (project_dir / "modules").mkdir()
        (project_dir / "README.md").write_text(f"# {name}\n\nA Verba project.\n\nRun with:\n```bash\nverba run main.vrb\n```\n", encoding="utf-8")
        
        print(f"Created Verba project in ./{name}/")
        print(f"cd {name} and run commands.")
        return 0
    except Exception as e:
        print(f"Failed to initialize project: {e}")
        return 1


VERSION = "1.0.0"

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
    inst_p = sub.add_parser("install", help="Install a package from the registry or a URL.")
    inst_p.add_argument("package", help="Name of the package, or a direct URL to a .vrb file.")

    # format
    fmt_p = sub.add_parser("format", help="Format a Verba script.")
    fmt_p.add_argument("file")

    # init
    init_p = sub.add_parser("init", help="Initialize a new Verba project.")
    init_p.add_argument("name", help="Name of the project directory.")

    # remove
    rm_p = sub.add_parser("remove", help="Remove an installed package.")
    rm_p.add_argument("package", help="Name of the package to remove.")

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
            return install_pkg(ns.package)
        if ns.command == "format":
            return format_file(Path(ns.file))
        if ns.command == "check":
            return check_file(Path(ns.file))
        if ns.command == "repl":
            return repl()
        if ns.command == "remove":
            return remove_pkg(ns.package)
        if ns.command == "init":
            return init_project(ns.name)
        if ns.command == "run":
            return run_file(Path(ns.file))
            
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
