"""
Import Service
Import memories from various formats
"""

import contextlib
import json
import sqlite3
import zipfile
from pathlib import Path
from typing import Any


class ImportService:
    """Service for importing memories"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    def import_from_json(
        self,
        input_path: str,
        mode: str = "merge",  # 'merge' or 'replace'
    ) -> dict[str, Any]:
        """
        Import memories from JSON

        Args:
            input_path:  Input JSON file
            mode: 'merge' (add new) or 'replace' (clear existing)

        Returns:
            Import summary
        """

        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Import file not found: {input_path}")

        with open(input_file) as f:
            data = json.load(f)

        memories = data.get("memories", [])

        if mode == "replace":
            self.conn.execute("DELETE FROM memories")

        imported = 0
        skipped = 0
        errors = 0

        for memory in memories:
            try:
                # Check if exists
                existing = self.conn.execute(
                    "SELECT id FROM memories WHERE id = ?", (memory["id"],)
                ).fetchone()

                if existing and mode == "merge":
                    skipped += 1
                    continue

                # Insert
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO memories (
                        id, tier, type, source, content, content_hash,
                        timestamp, project, file_path, language, tags, entities,
                        importance_score, access_count, created_at, last_accessed,
                        promoted_from, archived
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        memory.get("id"),
                        memory.get("tier"),
                        memory.get("type"),
                        memory.get("source"),
                        memory.get("content"),
                        memory.get("content_hash"),
                        memory.get("timestamp"),
                        memory.get("project"),
                        memory.get("file_path"),
                        memory.get("language"),
                        memory.get("tags"),
                        memory.get("entities"),
                        memory.get("importance_score"),
                        memory.get("access_count"),
                        memory.get("created_at"),
                        memory.get("last_accessed"),
                        memory.get("promoted_from"),
                        memory.get("archived", 0),
                    ),
                )

                imported += 1

            except Exception as e:
                errors += 1
                print(f"Error importing memory {memory.get('id')}: {e}")

        self.conn.commit()

        return {
            "success": True,
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total": len(memories),
        }

    def restore_full_backup(self, backup_path: str) -> dict[str, Any]:
        """Restore from full backup"""

        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Extract zip
        with zipfile.ZipFile(backup_file, "r") as zf:
            backup_json = zf.read("backup.json").decode("utf-8")
            data = json.loads(backup_json)

        # Clear existing data
        with contextlib.suppress(sqlite3.OperationalError):
            self.conn.execute("DELETE FROM entity_relationships")

        with contextlib.suppress(sqlite3.OperationalError):
            self.conn.execute("DELETE FROM memory_entities")

        with contextlib.suppress(sqlite3.OperationalError):
            self.conn.execute("DELETE FROM entities")

        self.conn.execute("DELETE FROM memories")

        # Restore memories
        for memory in data["memories"]:
            self.conn.execute(
                """
                INSERT INTO memories (
                    id, tier, type, source, content, content_hash,
                    timestamp, project, file_path, language, tags, entities,
                    importance_score, access_count, created_at, last_accessed,
                    promoted_from, archived
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory["id"],
                    memory["tier"],
                    memory["type"],
                    memory["source"],
                    memory["content"],
                    memory["content_hash"],
                    memory["timestamp"],
                    memory.get("project"),
                    memory.get("file_path"),
                    memory.get("language"),
                    memory.get("tags"),
                    memory.get("entities"),
                    memory["importance_score"],
                    memory["access_count"],
                    memory["created_at"],
                    memory.get("last_accessed"),
                    memory.get("promoted_from"),
                    memory["archived"],
                ),
            )

        # Restore entities
        if "entities" in data:
            for entity in data["entities"]:
                with contextlib.suppress(sqlite3.OperationalError):
                    self.conn.execute(
                        """
                        INSERT INTO entities (id, type, name, first_seen, last_seen, mention_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            entity["id"],
                            entity["type"],
                            entity["name"],
                            entity["first_seen"],
                            entity["last_seen"],
                            entity["mention_count"],
                        ),
                    )

        # Restore relationships
        if "relationships" in data:
            for rel in data["relationships"]:
                with contextlib.suppress(sqlite3.OperationalError):
                    self.conn.execute(
                        """
                        INSERT INTO entity_relationships (source_id, target_id, type, strength, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            rel["source_id"],
                            rel["target_id"],
                            rel["type"],
                            rel["strength"],
                            rel["created_at"],
                            rel["updated_at"],
                        ),
                    )

        self.conn.commit()

        return {
            "success": True,
            "memories_restored": len(data["memories"]),
            "entities_restored": len(data.get("entities", [])),
            "relationships_restored": len(data.get("relationships", [])),
        }
