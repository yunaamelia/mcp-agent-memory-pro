#!/usr/bin/env python3
"""
Test Entity Extractor
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "python"))

from services.ner_service import NERService


def test_entity_extraction():
    """Test entity extraction"""

    print("Testing Entity Extraction")
    print("=" * 50)

    ner = NERService()

    # Test code extraction
    code_sample = """
    import React from 'react';
    import axios from 'axios';

    async function fetchUserData(userId) {
        const response = await axios.get(`/api/users/${userId}`);
        return response.data;
    }

    class UserManager {
        constructor() {
            this.users = [];
        }
    }
    """

    entities = ner.extract_entities(
        code_sample, "code", {"project": "test-app", "language": "javascript"}
    )

    print("\nExtracted entities from code:")
    for entity in entities:
        print(
            f"  {entity['type']:10s} | {entity['name']:20s} | confidence: {entity['confidence']:.2f}"
        )

    # Test text extraction
    text_sample = "We discussed using React and TypeScript for the frontend, with authentication handled by JWT tokens."

    entities = ner.extract_entities(text_sample, "conversation", {})

    print("\nExtracted entities from text:")
    for entity in entities:
        print(
            f"  {entity['type']:10s} | {entity['name']:20s} | confidence: {entity['confidence']:.2f}"
        )

    print("\n✅ Entity extraction test passed!")


if __name__ == "__main__":
    test_entity_extraction()
