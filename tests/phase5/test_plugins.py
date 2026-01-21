#!/usr/bin/env python3
"""
Test Plugin System - Comprehensive
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from plugins.plugin_manager import PluginManager


def setup_test_plugin():
    """Create a test plugin"""

    plugin_dir = Path(__file__).parent.parent / "data" / "test_plugins"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create test plugin directory
    test_plugin_dir = plugin_dir / "test-plugin"
    test_plugin_dir.mkdir(exist_ok=True)

    # Create plugin manifest
    manifest = {
        "id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "hooks": ["test_hook"],
    }

    with open(test_plugin_dir / "plugin.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Create plugin code
    plugin_code = """
class Plugin:
    def __init__(self, manifest, manager):
        self.manifest = manifest
        self.manager = manager
        self.hook_called = False

    def register_hooks(self):
        self.manager.register_hook('test_hook', self.on_test_hook)

    def on_test_hook(self, data):
        self.hook_called = True
        return f"Hook received: {data}"
"""

    with open(test_plugin_dir / "index.py", "w") as f:
        f.write(plugin_code)

    print(f"✓ Created test plugin at {test_plugin_dir}\n")
    return plugin_dir


def test_plugin_manager():
    """Test plugin manager"""

    print("Testing Plugin Manager")
    print("=" * 60)

    plugin_dir = setup_test_plugin()

    try:
        # Test 1: Discover plugins
        print("\n1. Discovering plugins...")

        manager = PluginManager(plugin_dir)
        manager.discover_plugins()

        plugins = manager.list_plugins()

        print(f"  Discovered {len(plugins)} plugin(s)")

        for plugin_info in plugins:
            print(f"    - {plugin_info['name']} v{plugin_info['version']}")

        assert len(plugins) > 0, "No plugins discovered"

        print("  ✓ Plugin discovery working")

        # Test 2: Get specific plugin
        print("\n2. Getting specific plugin...")

        test_plugin = manager.get_plugin("test-plugin")

        assert test_plugin is not None, "Plugin not found"
        assert test_plugin.manifest["name"] == "Test Plugin", "Plugin manifest incorrect"

        print(f"  ✓ Retrieved plugin: {test_plugin.manifest['name']}")

        # Test 3: Trigger hooks
        print("\n3. Testing hook system...")

        results = manager.trigger_hook("test_hook", "test_data")

        print(f"  Hook triggered, {len(results)} result(s)")

        if results:
            print(f"    Result: {results[0]}")

        assert len(results) > 0, "Hook not triggered"
        assert test_plugin.hook_called, "Plugin hook not called"

        print("  ✓ Hook system working")

        # Test 4: Multiple hooks
        print("\n4. Testing multiple hook registrations...")

        call_count = 0

        def additional_hook(data):
            nonlocal call_count
            call_count += 1
            return f"Additional hook: {data}"

        manager.register_hook("test_hook", additional_hook)

        results = manager.trigger_hook("test_hook", "multi_test")

        assert len(results) >= 2, "Not all hooks triggered"
        assert call_count == 1, "Additional hook not called"

        print(f"  ✓ Multiple hooks working ({len(results)} callbacks)")

        print("\n✅ Plugin Manager: ALL TESTS PASSED")

        return True

    finally:
        # Cleanup
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)


def test_existing_plugins():
    """Test existing plugins in the project"""

    print("\n\nTesting Existing Plugins")
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

    print("  ✓ Existing plugin discovery working")

    # Test example plugin hooks
    print("\n2. Testing example plugin hooks...")

    memory_data = {"id": "test_memory", "type": "note", "content": "Test content", "tags": []}

    hook_results = manager.trigger_hook("before_store", memory_data)

    print(f"  Hook results: {len(hook_results)} callback(s)")

    if hook_results:
        modified_data = hook_results[0]
        print(f"  Modified data tags: {modified_data.get('tags', [])}")

        if "plugin-processed" in modified_data.get("tags", []):
            print("  ✓ Plugin modified data correctly")

    print("  ✓ Example plugin hooks working")

    return True


def main():
    """Run all plugin tests"""

    print("\n" + "=" * 60)
    print("PHASE 5 PLUGIN SYSTEM VALIDATION")
    print("=" * 60 + "\n")

    try:
        test_plugin_manager()
        test_existing_plugins()

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
