"""
Validate Phase 5 Implementation
Checks for existence and basic functionality of Phase 5 components
"""

import importlib.util
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
PYTHON_DIR = BASE_DIR / "python"
EXTENSIONS_DIR = BASE_DIR / "extensions"

sys.path.append(str(PYTHON_DIR))


def check_path(path: Path, name: str):
    if path.exists():
        print(f"✅ {name} exists")
        return True
    else:
        print(f"❌ {name} missing at {path}")
        return False


def validate_plugin_system():
    print("\n--- Validating Plugin System ---")

    # Check plugin manager
    pm_path = PYTHON_DIR / "plugins" / "plugin_manager.py"
    if not check_path(pm_path, "Plugin Manager"):
        return False

    # Check example plugin
    plugin_path = PYTHON_DIR / "plugins" / "example-plugin"
    if not check_path(plugin_path, "Example Plugin"):
        return False

    # Try importing PluginManager
    try:
        spec = importlib.util.spec_from_file_location("plugin_manager", pm_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pm = module.PluginManager(PYTHON_DIR / "plugins")
        pm.discover_plugins()

        if "example-plugin" in pm.plugins:
            print("✅ Example plugin loaded successfully")
        else:
            print("❌ Example plugin failed to load")
            return False

    except Exception as e:
        print(f"❌ Plugin system import failed: {e}")
        return False

    return True


def validate_extensions():
    print("\n--- Validating Extensions ---")

    # VSCode
    vscode_path = EXTENSIONS_DIR / "vscode"
    pkg_json = vscode_path / "package.json"
    src_ext = vscode_path / "src" / "extension.ts"

    check_path(pkg_json, "VSCode package.json")
    check_path(src_ext, "VSCode extension.ts")

    # Browser
    browser_path = EXTENSIONS_DIR / "browser"
    manifest = browser_path / "manifest.json"
    popup = browser_path / "popup" / "popup.html"

    check_path(manifest, "Browser manifest.json")
    check_path(popup, "Browser popup.html")

    return True


def validate_advanced_api():
    print("\n--- Validating Advanced API ---")

    # Check route file
    route_path = PYTHON_DIR / "api" / "routes" / "advanced.py"
    if not check_path(route_path, "Advanced Routes"):
        return False

    # Check usage in server.py
    server_path = PYTHON_DIR / "api" / "server.py"
    with open(server_path) as f:
        content = f.read()
        if "advanced.router" in content:
            print("✅ Advanced router registered in server.py")
        else:
            print("❌ Advanced router NOT registered in server.py")
            return False

    return True


def validate_caching():
    print("\n--- Validating Caching Service ---")

    cache_path = PYTHON_DIR / "services" / "caching_service.py"
    if not check_path(cache_path, "Caching Service"):
        return False

    try:
        spec = importlib.util.spec_from_file_location("caching_service", cache_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cache = module.CachingService()
        cache.set("test", "value")
        val = cache.get("test")

        if val == "value":
            print("✅ Caching service working (Get/Set)")
        else:
            print(f"❌ Caching service failed: Got {val}, expected 'value'")
            return False

    except Exception as e:
        print(f"❌ Caching service validation failed: {e}")
        return False

    return True


def main():
    print("🚀 Starting Phase 5 Validation")

    results = [
        validate_plugin_system(),
        validate_extensions(),
        validate_advanced_api(),
        validate_caching(),
    ]

    if all(results):
        print("\n✅ PHASE 5 VALIDATION SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n❌ PHASE 5 VALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
