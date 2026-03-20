import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import sys
import time
import threading
import hashlib


DEFAULT_REGISTRY_URL = "https://raw.githubusercontent.com/thegitguru/Verba/main/registry.json"


class Spinner:
    def __init__(self, message: str = "Working"):
        self.message = message
        self.running = False
        self.thread: threading.Thread | None = None

    def _spin(self):
        chars = "|/-\\"
        i = 0
        sys.stdout.write(f"{self.message}  ")
        while self.running:
            sys.stdout.write(f"\b{chars[i % 4]}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\b \r\n")
        sys.stdout.flush()

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.thread:
            self.thread.join()


def fetch_registry() -> dict:
    registry_url = os.environ.get("VERBA_REGISTRY", DEFAULT_REGISTRY_URL)
    
    # Local fallback testing override (Hardcoded specifically for your local dev environment)
    local_dev_reg = Path(r"d:\GitHub\Verba\registry.json")
    if registry_url == DEFAULT_REGISTRY_URL and local_dev_reg.exists():
        try:
            with open(local_dev_reg, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass # Fallback to web request
            
    with Spinner(f"Fetching registry from {registry_url}..."):
        try:
            req = urllib.request.Request(registry_url, headers={'User-Agent': 'Verba'})
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"Error fetching registry: {e}")
            return {}
            
    return result


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def download_package(name: str, url: str, expected_hash: str = "") -> tuple[bool, str]:
    if not name.endswith(".vrb"):
        name += ".vrb"
        
    global_cache_dir = Path.home() / ".verba" / "cache"
    global_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # We use a primitive cache key based on the URL hash
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_path = global_cache_dir / f"{name}_{cache_key}.vrb"
    
    content = None
    if cache_path.exists():
        content = cache_path.read_bytes()
        actual_hash = compute_sha256(content)
        if expected_hash and actual_hash != expected_hash:
            # Hash mismatch in cache, force refetch
            content = None
        else:
            print(f"Loaded {name} from global cache.")

    success = False
    err_msg = ""
    if content is None:
        with Spinner(f"Installing {name} from {url}..."):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Verba'})
                with urllib.request.urlopen(req) as response:
                    content = response.read()
                
                # Check integrity before saving
                actual_hash = compute_sha256(content)
                if expected_hash and actual_hash != expected_hash:
                    raise Exception(f"Checksum mismatch! Expected {expected_hash}, got {actual_hash}")
                    
                # Save to cache
                cache_path.write_bytes(content)
                success = True
            except Exception as e:
                err_msg = str(e)
    else:
        success = True

    if success and content is not None:
        modules_dir = Path("modules")
        modules_dir.mkdir(exist_ok=True)
        (modules_dir / name).write_bytes(content)
        actual_hash = compute_sha256(content)
        print(f"Successfully installed to {modules_dir / name} (sha256: {actual_hash[:8]})")
        return True, actual_hash
    else:
        print(f"I failed to install the package: {err_msg}")
        return False, ""


def _update_verba_json(pkg_key: str, url: str, version: str = "unknown", package_hash: str = ""):
    vjson_path = Path("verba.json")
    if not vjson_path.exists():
        return
        
    try:
        with open(vjson_path, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        
        if "dependencies" not in project_data:
            project_data["dependencies"] = {}
        
        project_data["dependencies"][pkg_key] = {
            "version": version,
            "url": url
        }
        
        with open(vjson_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, indent=2)
            
        print(f"Updated verba.json with dependency '{pkg_key}' (v{version})")
    except Exception as e:
        print(f"Warning: Could not update verba.json: {e}")
        
    # Generate verba-lock.json with checksum integrity
    lock_path = Path("verba-lock.json")
    lock_data = {"dependencies": {}}
    if lock_path.exists():
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
        except Exception:
            pass
            
    lock_data["dependencies"][pkg_key] = {
        "version": version,
        "url": url,
        "integrity": f"sha256-{package_hash}"
    }
    
    try:
        with open(lock_path, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not update verba-lock.json: {e}")


def install(package: str | None = None) -> int:
    # If no package specified, install from verba.json
    if package is None:
        vjson_path = Path("verba.json")
        if not vjson_path.exists():
            print("Error: No package specified and no verba.json found.")
            return 1
            
        try:
            with open(vjson_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies", {})
            if not deps:
                print("No dependencies found in verba.json.")
                return 0
                
            # Load lockfile for expected hashes
            lockfile_hashes = {}
            lock_path = Path("verba-lock.json")
            if lock_path.exists():
                try:
                    with open(lock_path, "r", encoding="utf-8") as lf:
                        lock_deps = json.load(lf).get("dependencies", {})
                        for l_name, l_info in lock_deps.items():
                            val = str(l_info.get("integrity", ""))
                            if val.startswith("sha256-"):
                                lockfile_hashes[l_name] = val.split("-")[1]
                except Exception:
                    pass
                    
            for dep_name, dep_info in deps.items():
                dep_url = dep_info["url"] if isinstance(dep_info, dict) else dep_info
                expected_hash = lockfile_hashes.get(dep_name, "")
                download_package(dep_name, dep_url, expected_hash)
            return 0
        except Exception as e:
            print(f"Error reading verba.json: {e}")
            return 1

    is_url = package.startswith("http://") or package.startswith("https://")
    
    if is_url:
        url = str(package)
        version = "unknown"
        parsed = urlparse(url)
        name = Path(parsed.path).name
        if not name:
            print(f"Error: Could not determine package name for URL: {url}")
            return 1
    else:
        registry = fetch_registry()
        if not registry:
            return 1
            
        if package not in registry:
            print(f"Error: Package '{package}' not found in registry.")
            return 1
            
        registry_entry = registry[package]
        expected_hash = ""
        if isinstance(registry_entry, dict):
            url = str(registry_entry.get("url", ""))
            version = str(registry_entry.get("version", "unknown"))
            expected_hash = str(registry_entry.get("hash", ""))
        else:
            url = str(registry_entry)
            version = "unknown"
            
        name = str(package)

    success, pkg_hash = download_package(name, url, expected_hash)
    if success:
        pkg_key = str(name[:-4]) if name.endswith(".vrb") else str(name)
        _update_verba_json(pkg_key, url, version, pkg_hash)
        return 0
    return 1


def remove(package: str) -> int:
    name = package
    if not name.endswith(".vrb"):
        name += ".vrb"
        
    modules_dir = Path("modules")
    pkg_path = modules_dir / name
    
    with Spinner(f"Removing {package}..."):
        time.sleep(0.5) # for aesthetics
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


def update(package: str | None = None) -> int:
    registry = fetch_registry()
    if not registry:
        return 1

    vjson_path = Path("verba.json")
    if not vjson_path.exists():
        print("Error: No verba.json found to update.")
        return 1

    try:
        with open(vjson_path, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        deps = project_data.get("dependencies", {})
    except Exception as e:
        print(f"Error reading verba.json: {e}")
        return 1

    to_update = [package] if package else list(deps.keys())
    
    updated_count = 0
    for pkg_name in to_update:
        if pkg_name not in deps:
            print(f"Package '{pkg_name}' is not in verba.json.")
            continue
            
        if pkg_name not in registry:
            print(f"Package '{pkg_name}' not found in registry (cannot update).")
            continue
            
        reg_entry = registry[pkg_name]
        reg_url = ""
        reg_version = "unknown"
        if isinstance(reg_entry, dict):
            reg_url = str(reg_entry.get("url", ""))
            reg_version = str(reg_entry.get("version", "unknown"))
        else:
            reg_url = str(reg_entry)
            
        curr_dep = deps[pkg_name]
        curr_version = curr_dep.get("version", "unknown") if isinstance(curr_dep, dict) else "unknown"
        
        if curr_version != "unknown" and reg_version != "unknown" and curr_version == reg_version:
            import sys
            sys.stdout.write(f"'{pkg_name}' is already up-to-date (v{curr_version}).\n")
            continue
            
        expected_hash = str(reg_entry.get("hash", "")) if isinstance(reg_entry, dict) else ""
        success, pkg_hash = download_package(str(pkg_name), reg_url, expected_hash)
        if success:
            _update_verba_json(str(pkg_name), reg_url, reg_version, pkg_hash)
            updated_count += 1
            
    if updated_count == 0 and not package:
        print("All packages are up to date.")
    return 0


def list_pkgs() -> int:
    modules_dir = Path("modules")
    if not modules_dir.exists() or not modules_dir.is_dir():
        print("No packages installed (modules/ directory not found).")
        return 0
        
    pkgs = [p.name for p in modules_dir.iterdir() if p.name.endswith(".vrb")]
    if not pkgs:
        print("No packages installed.")
        return 0
        
    print("Installed Verba Packages:")
    
    # Try to load versions from verba.json
    versions = {}
    vjson_path = Path("verba.json")
    if vjson_path.exists():
        try:
            with open(vjson_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies", {})
            for k, v in deps.items():
                if isinstance(v, dict) and "version" in v:
                    versions[k] = v["version"]
        except Exception:
            pass

    for pkg in pkgs:
        name = pkg[:-4]
        ver = versions.get(name, "unknown")
        print(f"  - {name} (v{ver})")
        
    return 0


def init(name: str) -> int:
    try:
        project_dir = Path(name)
        if project_dir.exists():
            print(f"Error: Directory '{name}' already exists.")
            return 1
            
        project_dir.mkdir(parents=True)
        (project_dir / "main.vrb").write_text("say \"Hello from Verba!\".\n", encoding="utf-8")
        (project_dir / "verba.json").write_text(f'{{\n  "name": "{name}",\n  "version": "1.0.0",\n  "dependencies": {{}}\n}}\n', encoding="utf-8")
        (project_dir / "modules").mkdir()
        (project_dir / "README.md").write_text(f"# {name}\n\nA Verba project.\n\nRun with:\n```bash\nverba run main.vrb\n```\n", encoding="utf-8")
        
        print(f"Created Verba project in ./{name}/")
        print(f"cd {name} and run commands.")
        return 0
    except Exception as e:
        print(f"Failed to initialize project: {e}")
        return 1
