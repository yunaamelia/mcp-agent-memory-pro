"""
Claude API Client
For summarization using Claude
"""

import sys
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.append(str(Path(__file__).parent.parent))

from config import CLAUDE_API_KEY, CLAUDE_MAX_TOKENS, CLAUDE_MODEL


class ClaudeClient:
    """Client for Claude API"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or CLAUDE_API_KEY

        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = CLAUDE_MODEL
        self.max_tokens = CLAUDE_MAX_TOKENS

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def summarize_memory(self, content: str, memory_type: str, context: dict[str, Any]) -> str:
        """
        Summarize a memory while preserving key information

        Args:
            content: Original memory content
            memory_type:  Type of memory (code, note, etc.)
            context: Additional context (project, tags, etc.)

        Returns:
            Summarized content
        """

        # Build prompt based on memory type
        if memory_type == "code":
            prompt = self._build_code_summary_prompt(content, context)
        elif memory_type == "conversation":
            prompt = self._build_conversation_summary_prompt(content, context)
        else:
            prompt = self._build_general_summary_prompt(content, context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            summary = response.content[0].text.strip()
            return summary

        except Exception as e:
            raise Exception(f"Claude API error: {e}")

    def _build_code_summary_prompt(self, content: str, context: dict[str, Any]) -> str:
        """Build prompt for code summarization"""

        context_str = ""
        if context.get("project"):
            context_str += f"\nProject: {context['project']}"
        if context.get("file_path"):
            context_str += f"\nFile: {context['file_path']}"
        if context.get("language"):
            context_str += f"\nLanguage: {context['language']}"

        return f"""Summarize the following code snippet concisely while preserving:
1. Main function/class names
2. Key functionality
3. Important patterns or techniques used
4. Any notable dependencies or imports

{context_str}

Code:
```
{content[:2000]}  # Limit to avoid token limits
```

Provide a concise summary (max 200 words) that captures the essence and key details."""

    def _build_conversation_summary_prompt(self, content: str, context: dict[str, Any]) -> str:
        """Build prompt for conversation summarization"""

        return f"""Summarize the following technical discussion concisely while preserving:
1. Main decisions made
2. Key technical points discussed
3. Action items or conclusions
4. Important context

Discussion:
{content[:3000]}

Provide a concise summary (max 200 words) that captures the key points and decisions."""

    def _build_general_summary_prompt(self, content: str, context: dict[str, Any]) -> str:
        """Build prompt for general summarization"""

        return f"""Summarize the following content concisely while preserving:
1. Main topic or purpose
2. Key information or facts
3. Important context or details

Content:
{content[:3000]}

Provide a concise summary (max 200 words) that captures the essential information."""

    def batch_summarize(self, memories: list[dict[str, Any]]) -> dict[str, str]:
        """
        Summarize multiple memories

        Args:
            memories: List of memory dicts with 'id', 'content', 'type', 'context'

        Returns:
            Dict mapping memory_id to summary
        """

        results = {}

        for memory in memories:
            try:
                summary = self.summarize_memory(
                    memory["content"], memory["type"], memory.get("context", {})
                )
                results[memory["id"]] = summary

            except Exception as e:
                # Log error but continue with others
                print(f"Error summarizing {memory['id']}: {e}")
                results[memory["id"]] = None

        return results
