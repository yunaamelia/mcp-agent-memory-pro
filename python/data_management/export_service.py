"""
Export Service
Export memories to various formats
"""

import csv
import json
import sqlite3
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ExportService:
    """Service for exporting memories"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection

    def export_to_json(
        self,
        output_path: str,
        filters: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """
        Export memories to JSON

        Args:
            output_path: Output file path
            filters: Optional filters (project, type, tier, etc.)
            include_metadata: Include export metadata

        Returns:
            Export summary
        """

        # Build query
        query = "SELECT * FROM memories WHERE archived = 0"
        params = []

        if filters:
            if filters.get("project"):
                query += " AND project = ?"
                params.append(filters["project"])

            if filters.get("type"):
                query += " AND type = ?"
                params.append(filters["type"])

            if filters.get("tier"):
                query += " AND tier = ?"
                params.append(filters["tier"])

        cursor = self.conn.execute(query, params)
        memories = [dict(row) for row in cursor.fetchall()]

        # Prepare export data
        export_data = {"memories": memories, "count": len(memories)}

        if include_metadata:
            export_data["metadata"] = {
                "exported_at": datetime.now(UTC).isoformat(),
                "source": "MCP Agent Memory Pro",
                "version": "1.0.0",
                "filters": filters or {},
            }

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        return {
            "success": True,
            "output_path": str(output_file),
            "count": len(memories),
            "size_bytes": output_file.stat().st_size,
        }

    def export_to_csv(
        self,
        output_path: str,
        filters: dict[str, Any] | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Export memories to CSV"""

        # Default columns
        if not columns:
            columns = ["id", "type", "tier", "content", "project", "timestamp", "importance_score"]

        # Build query
        query = f"SELECT {', '.join(columns)} FROM memories WHERE archived = 0"
        params = []

        if filters:
            if filters.get("project"):
                query += " AND project = ?"
                params.append(filters["project"])

            if filters.get("type"):
                query += " AND type = ?"
                params.append(filters["type"])

        cursor = self.conn.execute(query, params)
        memories = cursor.fetchall()

        # Write CSV
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(columns)

            # Data
            for memory in memories:
                writer.writerow(memory)

        return {
            "success": True,
            "output_path": str(output_file),
            "count": len(memories),
            "size_bytes": output_file.stat().st_size,
        }

    def export_full_backup(self, output_path: str) -> dict[str, Any]:
        """Export complete backup (memories + entities + relationships)"""

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Collect all data
        backup_data = {
            "metadata": {
                "exported_at": datetime.now(UTC).isoformat(),
                "version": "1.0.0",
                "backup_type": "full",
            },
            "memories": [],
            "entities": [],
            "relationships": [],
            "statistics": {},
        }

        # Export memories
        cursor = self.conn.execute("SELECT * FROM memories")
        backup_data["memories"] = [dict(row) for row in cursor.fetchall()]

        # Export entities
        cursor = self.conn.execute("SELECT * FROM entities")
        try:
            backup_data["entities"] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Handle case where table might not exist in early versions
            backup_data["entities"] = []

        # Export relationships
        try:
            cursor = self.conn.execute("SELECT * FROM entity_relationships")
            backup_data["relationships"] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            backup_data["relationships"] = []

        # Export statistics
        try:
            cursor = self.conn.execute("SELECT * FROM statistics")
            backup_data["statistics"] = {row["key"]: row["value"] for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            backup_data["statistics"] = {}

        # Create zip file
        zip_path = output_file.with_suffix(".zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write JSON
            json_data = json.dumps(backup_data, indent=2, default=str)
            zf.writestr("backup.json", json_data)

            # Write metadata
            metadata = {
                "created_at": datetime.now(UTC).isoformat(),
                "memory_count": len(backup_data["memories"]),
                "entity_count": len(backup_data["entities"]),
                "relationship_count": len(backup_data["relationships"]),
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        return {
            "success": True,
            "output_path": str(zip_path),
            "memory_count": len(backup_data["memories"]),
            "entity_count": len(backup_data["entities"]),
            "size_bytes": zip_path.stat().st_size,
        }
