"""
Example Plugin
Demonstrates plugin functionality
"""


class Plugin:
    """Example plugin implementation"""

    def __init__(self, manifest, manager):
        self.manifest = manifest
        self.manager = manager

    def register_hooks(self):
        """Register plugin hooks"""

        # Hook into memory storage
        self.manager.register_hook("before_store", self.on_before_store)

        # Hook into search results
        self.manager.register_hook("after_search", self.on_after_search)

    def on_before_store(self, memory_data):
        """Called before storing a memory"""

        print(f"Example plugin: Before storing {memory_data.get('type')} memory")

        # Could modify memory_data here
        # For example, add custom tags
        if "tags" not in memory_data:
            memory_data["tags"] = []

        memory_data["tags"].append("plugin-processed")

        return memory_data

    def on_after_search(self, query, results):
        """Called after search"""

        print(f"Example plugin: Search returned {len(results)} results")

        # Could modify or filter results
        return results
