import sys
import time
from pathlib import Path

import pytest

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from python.plugins.plugin_manager import PluginManager
from python.services.caching_service import CachingService

# --- Plugin System Tests ---


@pytest.fixture
def plugin_manager():
    # Point to the actual plugins dir in the project
    base_dir = Path(__file__).parent.parent.parent / "python" / "plugins"
    return PluginManager(base_dir)


def test_plugin_discovery(plugin_manager):
    plugin_manager.discover_plugins()
    assert len(plugin_manager.plugins) > 0
    assert "example-plugin" in plugin_manager.plugins


def test_plugin_hooks(plugin_manager):
    plugin_manager.discover_plugins()

    # helper to capture hook output
    results = []

    def hook_callback(data):
        results.append(data)
        return data

    # Register a manual hook to test trigger mechanism
    plugin_manager.register_hook("test_hook", hook_callback)

    # Trigger
    plugin_manager.trigger_hook("test_hook", "test_data")
    assert "test_data" in results

    # Test example plugin before_store hook
    # The example plugin appends "plugin-processed" tag
    memory_data = {"type": "note", "content": "foo"}
    res = plugin_manager.trigger_hook("before_store", memory_data)

    # We expect the plugin to have modified the data (it returns the modified data)
    # The trigger_hook returns a list of results from all callbacks
    assert len(res) > 0
    assert "tags" in res[0]
    assert "plugin-processed" in res[0]["tags"]


# --- Caching Service Tests ---


@pytest.fixture
def cache():
    c = CachingService(max_size=5, default_ttl=1)
    yield c
    c.stop()


def test_cache_set_get(cache):
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar"


def test_cache_expiry(cache):
    cache.set("quick", "gone", ttl=0.1)
    assert cache.get("quick") == "gone"
    time.sleep(0.2)
    assert cache.get("quick") is None


def test_cache_lru_eviction(cache):
    # max_size is 5
    for i in range(5):
        cache.set(f"key{i}", f"val{i}")

    assert cache.get("key0") == "val0"

    # Add 6th item
    cache.set("key5", "val5")

    # key0 should NOT be evicted because we just accessed it (LRU) => key1 should be evicted?
    # Wait, LRU policy: "Least Recently Used".
    # Accessed key0 => key0 is most recent.
    # Added 0..4. Accessed 0. Cache state (old->new): 1, 2, 3, 4, 0.
    # Add 5. Evict 1.

    assert cache.get("key1") is None
    assert cache.get("key0") == "val0"
    assert cache.get("key5") == "val5"
