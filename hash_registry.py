import json
import hashlib
import urllib.request
from pathlib import Path

def get_hash(url):
    print(f"Fetching {url}...", end=" ", flush=True)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Verba'})
        with urllib.request.urlopen(req) as response:
            content = response.read()
        sha_hash = hashlib.sha256(content).hexdigest()
        print(f"OK ({sha_hash[:8]})")
        return sha_hash
    except Exception as e:
        print(f"Failed! {e}")
        return ""

def main():
    reg_path = Path("registry.json")
    if not reg_path.exists():
        print("registry.json not found!")
        return
        
    with open(reg_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    print("Updating hashes in registry.json...")
    for pkg_name, pkg_data in registry.items():
        print(f"\nProcessing package: {pkg_name}")
        if isinstance(pkg_data, dict):
            # Update root hash
            url = pkg_data.get("url")
            if url:
                h = get_hash(url)
                if h:
                    pkg_data["hash"] = h
            
            # Update specific versions hash
            if "versions" in pkg_data:
                for ver, ver_info in pkg_data["versions"].items():
                    if isinstance(ver_info, dict):
                        v_url = ver_info.get("url")
                        if v_url:
                            v_h = get_hash(v_url)
                            if v_h:
                                ver_info["hash"] = v_h
        else:
            print(f"Package {pkg_name} is in legacy format. Converting to dict...")
            url = pkg_data
            h = get_hash(url)
            registry[pkg_name] = {
                "version": "unknown",
                "url": url,
                "hash": h
            }
            
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
        
    print("\nSuccessfully dynamically added hashes to registry.json!")

if __name__ == "__main__":
    main()
