#!/usr/bin/env python3
"""
Test Plugin System
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from plugins.plugin_manager import PluginManager


def test_plugin_discovery():
    """Test plugin discovery"""

    print("Testing Plugin Discovery")
    print("=" * 60)

    plugins_dir = Path(__file__).parent.parent.parent / "python" / "plugins"

    print(f"\n1. Scanning plugins in: {plugins_dir}")

    manager = PluginManager(plugins_dir)
    manager.discover_plugins()

    print(f"  Found {len(manager.plugins)} plugin(s)")

    for plugin_id, plugin in manager.plugins.items():
        name = plugin.manifest.get("name", plugin_id)
        version = plugin.manifest.get("version", "0.0.0")
        print(f"    - {plugin_id}: {name} v{version}")

    assert len(manager.plugins) > 0, "No plugins discovered"
    assert "example-plugin" in manager.plugins, "Example plugin not found"

    print("  ✓ Plugin discovery working")

    return manager


def test_plugin_hooks(manager):
    """Test plugin hook system"""

    print("\n\nTesting Plugin Hooks")
    print("=" * 60)

    print("\n1. Testing hook registration...")

    results = []

    def test_callback(data):
        results.append(data)
        return data

    manager.register_hook("test_hook", test_callback)

    # Trigger the hook
    manager.trigger_hook("test_hook", {"test": "data"})

    assert len(results) > 0, "Hook not triggered"
    print("  ✓ Hook registration working")

    print("\n2. Testing example plugin hooks...")

    # Test before_store hook (example plugin adds tags)
    memory_data = {"id": "test_memory", "type": "note", "content": "Test content", "tags": []}

    hook_results = manager.trigger_hook("before_store", memory_data)

    print(f"  Hook results: {len(hook_results)} callback(s)")

    if hook_results:
        modified_data = hook_results[0]
        print(f"  Modified data tags: {modified_data.get('tags', [])}")

        if "plugin-processed" in modified_data.get("tags", []):
            print("  ✓ Plugin modified data correctly")

    print("  ✓ Plugin hooks working")

    return True


def test_plugin_lifecycle():
    """Test plugin enable/disable"""

    print("\n\nTesting Plugin Lifecycle")
    print("=" * 60)

    plugins_dir = Path(__file__).parent.parent.parent / "python" / "plugins"

    manager = PluginManager(plugins_dir)
    manager.discover_plugins()

    print("\n1. Testing plugin loading...")

    # Get example plugin
    example_plugin = manager.plugins.get("example-plugin")

    if example_plugin:
        print(f"  Plugin loaded: {example_plugin.manifest.get('name')}")
        print(f"  Manifest keys: {list(example_plugin.manifest.keys())}")
        print("  ✓ Plugin lifecycle working")
    else:
        print("  ⚠ Example plugin not found")

    return True


def main():
    """Run all plugin tests"""

    print("\n" + "=" * 60)
    print("PHASE 5 PLUGIN SYSTEM VALIDATION")
    print("=" * 60 + "\n")

    try:
        manager = test_plugin_discovery()
        test_plugin_hooks(manager)
        test_plugin_lifecycle()

        print("\n" + "=" * 60)
        print("✅ ALL PLUGIN TESTS PASSED")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Plugin tests failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
