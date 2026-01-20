"""
Named Entity Recognition Service
Extracts entities from code and text memories
"""

import re
from typing import Any


class NERService:
    """Service for extracting entities from memories"""

    def __init__(self):
        # Code patterns
        self.function_pattern = re.compile(
            r"\b(?:function|def|async\s+function|const|let|var)\s+(\w+)\s*\("
        )
        self.class_pattern = re.compile(r"\bclass\s+(\w+)\s*[{(: )]")
        self.import_pattern = re.compile(
            r'\b(?:import|from|require)\s+[\'"]?([a-zA-Z0-9_/.-]+)[\'"]?'
        )
        self.variable_pattern = re.compile(r"\b(?:const|let|var)\s+(\w+)\s*=")

        # File patterns
        self.file_pattern = re.compile(
            r'(?:^|[\s\'"(])([a-zA-Z0-9_-]+/[a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+)'
        )

        # Technical terms (common keywords)
        self.tech_terms = {
            "react",
            "vue",
            "angular",
            "node",
            "express",
            "fastapi",
            "django",
            "typescript",
            "javascript",
            "python",
            "rust",
            "go",
            "java",
            "database",
            "api",
            "rest",
            "graphql",
            "sql",
            "nosql",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "authentication",
            "authorization",
            "jwt",
            "oauth",
            "test",
            "testing",
            "unit",
            "integration",
            "e2e",
            "bug",
            "error",
            "exception",
            "debug",
        }

    def extract_entities(
        self, content: str, memory_type: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extract entities from memory content

        Returns:
            List of entities:  [{'type': str, 'name': str, 'confidence': float}, ...]
        """

        entities = []

        if memory_type == "code":
            entities.extend(self._extract_code_entities(content))

        # Extract file references
        entities.extend(self._extract_file_entities(content))

        # Extract technical terms
        entities.extend(self._extract_tech_terms(content))

        # Add context entities
        if context.get("project"):
            entities.append({"type": "project", "name": context["project"], "confidence": 1.0})

        if context.get("language"):
            entities.append({"type": "language", "name": context["language"], "confidence": 1.0})

        # Deduplicate and filter
        unique_entities = self._deduplicate_entities(entities)

        return unique_entities

    def _extract_code_entities(self, content: str) -> list[dict[str, Any]]:
        """Extract code-specific entities"""

        entities = []

        # Functions
        for match in self.function_pattern.finditer(content):
            entities.append({"type": "function", "name": match.group(1), "confidence": 0.95})

        # Classes
        for match in self.class_pattern.finditer(content):
            entities.append({"type": "class", "name": match.group(1), "confidence": 0.95})

        # Imports
        for match in self.import_pattern.finditer(content):
            entities.append({"type": "import", "name": match.group(1), "confidence": 0.85})

        # Variables (less confident)
        for match in self.variable_pattern.finditer(content):
            var_name = match.group(1)
            # Skip common short names
            if len(var_name) > 3 and not var_name.startswith("_"):
                entities.append({"type": "variable", "name": var_name, "confidence": 0.6})

        return entities

    def _extract_file_entities(self, content: str) -> list[dict[str, Any]]:
        """Extract file path entities"""

        entities = []

        for match in self.file_pattern.finditer(content):
            file_path = match.group(1)
            entities.append({"type": "file", "name": file_path, "confidence": 0.8})

        return entities

    def _extract_tech_terms(self, content: str) -> list[dict[str, Any]]:
        """Extract technical terms and concepts"""

        entities = []
        content_lower = content.lower()

        for term in self.tech_terms:
            if re.search(r"\b" + re.escape(term) + r"\b", content_lower):
                entities.append({"type": "concept", "name": term, "confidence": 0.7})

        return entities

    def _deduplicate_entities(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate entities, keeping highest confidence"""

        entity_map = {}

        for entity in entities:
            key = (entity["type"], entity["name"].lower())

            if key not in entity_map or entity["confidence"] > entity_map[key]["confidence"]:
                entity_map[key] = entity

        # Filter by confidence threshold
        filtered = [e for e in entity_map.values() if e["confidence"] >= 0.5]

        return filtered
