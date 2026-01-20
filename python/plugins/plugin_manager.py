"""
Plugin Manager
Extensible plugin system for custom functionality
"""

import importlib
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional


class PluginManager:
    """Manages plugins and extensions"""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugins: dict[str, Plugin] = {}
        self.hooks: dict[str, list[Callable]] = {}

    def discover_plugins(self):
        """Discover and load all plugins"""

        if not self.plugin_dir.exists():
            return

        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue

            # Check for plugin.json
            manifest_path = plugin_path / "plugin.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)

                plugin = self._load_plugin(plugin_path, manifest)
                if plugin:
                    self.plugins[manifest["id"]] = plugin
                    print(f"Loaded plugin: {manifest['name']}")
            except Exception as e:
                print(f"Failed to load plugin {plugin_path.name}: {e}")

    def _load_plugin(self, plugin_path: Path, manifest: dict[str, Any]) -> Optional["Plugin"]:
        """Load a single plugin"""

        # Import plugin module
        spec = importlib.util.spec_from_file_location(manifest["id"], plugin_path / "index.py")

        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get plugin class
        plugin_class = getattr(module, "Plugin", None)
        if not plugin_class:
            return None

        # Instantiate plugin
        plugin = plugin_class(manifest, self)

        # Register hooks
        if hasattr(plugin, "register_hooks"):
            plugin.register_hooks()

        return plugin

    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""

        if hook_name not in self.hooks:
            self.hooks[hook_name] = []

        self.hooks[hook_name].append(callback)

    def trigger_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        """Trigger a hook and collect results"""

        results = []

        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"Hook {hook_name} callback failed: {e}")

        return results

    def get_plugin(self, plugin_id: str) -> Optional["Plugin"]:
        """Get a loaded plugin"""
        return self.plugins.get(plugin_id)

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all loaded plugins"""

        return [
            {
                "id": plugin_id,
                "name": plugin.manifest["name"],
                "version": plugin.manifest["version"],
                "description": plugin.manifest.get("description", ""),
            }
            for plugin_id, plugin in self.plugins.items()
        ]


class Plugin:
    """Base plugin class"""

    def __init__(self, manifest: dict[str, Any], manager: PluginManager):
        self.manifest = manifest
        self.manager = manager

    def register_hooks(self):
        """Register hooks - override in subclass"""
        pass
