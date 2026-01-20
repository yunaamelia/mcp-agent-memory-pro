"""
Summarization Service
Uses Claude API to summarize memory content
"""

import logging
import sys
from pathlib import Path

from anthropic import Anthropic

sys.path.append(str(Path(__file__).parent.parent))

from config import CLAUDE_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL


class SummarizationService:
    """Service for generating summaries using LLM"""

    def __init__(self):
        self.logger = logging.getLogger("SummarizationService")

        if CLAUDE_API_KEY:
            self.client = Anthropic(api_key=CLAUDE_API_KEY)
            self.enabled = True
        else:
            self.logger.warning("CLAUDE_API_KEY not found. Summarization disabled.")
            self.client = None
            self.enabled = False

    def summarize(self, content: str, context: str = "") -> str | None:
        """Generate summary of content"""

        if not self.enabled or not content:
            return None

        try:
            prompt = f"""
            Please provide a concise summary of the following memory content.
            Capture key technical details, decisions, and entities.
            Keep it under 3 sentences.

            Context: {context}

            Content:
            {content[:4000]}  # Truncate to avoid context limits
            """

            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text

        except Exception as e:
            self.logger.error(f"Summarization failed: {e}")
            return None

    def generate_title(self, content: str) -> str | None:
        """Generate a short title for the memory"""

        if not self.enabled or not content:
            return None

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate a 3-5 word title for this content: {content[:1000]}",
                    }
                ],
            )

            return response.content[0].text.strip('"').strip()

        except Exception as e:
            self.logger.error(f"Title generation failed: {e}")
            return None
