"""
Centralized Claude API client with cost tracking and fallback.
"""
import anthropic
from typing import Optional, AsyncIterator
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = settings.CLAUDE_MODEL
        self.fast_model = settings.CLAUDE_FAST_MODEL

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_fast_model: bool = False,
    ) -> str:
        """Simple completion — returns text response."""
        selected_model = model or (self.fast_model if use_fast_model else self.default_model)
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": selected_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        try:
            response = await self.client.messages.create(**kwargs)
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        use_fast_model: bool = False,
    ) -> dict:
        """Completion that returns parsed JSON."""
        import json
        import re

        system_with_json = (system or "") + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        text = await self.complete(
            prompt=prompt,
            system=system_with_json.strip(),
            model=model,
            max_tokens=max_tokens,
            temperature=0.2,
            use_fast_model=use_fast_model,
        )

        # Strip markdown code blocks if present
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nRaw response: {text[:500]}")
            raise ValueError(f"Claude returned invalid JSON: {e}")

    async def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 8192,
        use_fast_model: bool = False,
    ) -> AsyncIterator[str]:
        """Streaming completion."""
        selected_model = model or (self.fast_model if use_fast_model else self.default_model)
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": selected_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text


# Singleton instance
claude = ClaudeClient()
