import asyncio
import json
import os
import random
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


class LLMError(Exception):
    pass


class PayloadTooLargeError(LLMError):
    pass


class RateLimitError(LLMError):
    pass


def _clean_text(text: str) -> str:
    return " ".join((text or "").split())


def chunk_text(
    text: str,
    max_chars: int = 12000,
    overlap: int = 500,
) -> List[str]:
    """
    Split large source text into bounded semantic chunks.

    The overlap preserves context between adjacent chunks.
    """
    text = _clean_text(text)

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + max_chars, length)

        if end < length:
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunks.append(text[start:end])

        if end >= length:
            break

        start = max(end - overlap, start + 1)

    return chunks


def extract_json(text: str) -> Dict[str, Any]:
    """
    Extract JSON from normal JSON output or fenced ```json output.
    """
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])

        raise LLMError("LLM did not return valid JSON")


class LLMOrchestrator:

    def __init__(self):
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))

        self.providers = [
            "gemini",
            "groq",
            "deepseek",
        ]

        self._semaphore = asyncio.Semaphore(
            int(os.getenv("LLM_MAX_CONCURRENCY", "5"))
        )

        self._clients = {}

    def _get_gemini(self):
        if "gemini" not in self._clients:
            from google import genai

            key = os.getenv("GEMINI_API_KEY")

            if not key:
                raise LLMError("GEMINI_API_KEY is not configured")

            self._clients["gemini"] = genai.Client(api_key=key)

        return self._clients["gemini"]

    def _get_groq(self):
        if "groq" not in self._clients:
            from groq import Groq

            key = os.getenv("GROQ_API_KEY")

            if not key:
                raise LLMError("GROQ_API_KEY is not configured")

            self._clients["groq"] = Groq(api_key=key)

        return self._clients["groq"]

    def _get_deepseek(self):
        if "deepseek" not in self._clients:
            from openai import OpenAI

            key = os.getenv("DEEPSEEK_API_KEY")

            if not key:
                raise LLMError("DEEPSEEK_API_KEY is not configured")

            self._clients["deepseek"] = OpenAI(
                api_key=key,
                base_url="https://api.deepseek.com",
            )

        return self._clients["deepseek"]

    def _is_rate_limit(self, error: Exception) -> bool:
        text = str(error).lower()

        return (
            "429" in text
            or "rate limit" in text
            or "too many requests" in text
        )

    def _is_payload_error(self, error: Exception) -> bool:
        text = str(error).lower()

        return (
            "413" in text
            or "payload too large" in text
            or "context length" in text
            or "context window" in text
            or "too long" in text
        )

    async def _gemini(self, prompt: str) -> str:
        client = self._get_gemini()

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text

    async def _groq(self, prompt: str) -> str:
        client = self._get_groq()

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0,
        )

        return response.choices[0].message.content

    async def _deepseek(self, prompt: str) -> str:
        client = self._get_deepseek()

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0,
        )

        return response.choices[0].message.content

    async def _call_provider(
        self,
        provider: str,
        prompt: str,
    ) -> str:

        if provider == "gemini":
            return await asyncio.wait_for(
                self._gemini(prompt),
                timeout=self.timeout,
            )

        if provider == "groq":
            return await asyncio.wait_for(
                self._groq(prompt),
                timeout=self.timeout,
            )

        if provider == "deepseek":
            return await asyncio.wait_for(
                self._deepseek(prompt),
                timeout=self.timeout,
            )

        raise LLMError(f"Unknown provider: {provider}")

    async def extract(
        self,
        source_text: str,
        source_url: str,
        schema_description: str,
    ) -> Dict[str, Any]:

        chunks = chunk_text(source_text)

        if not chunks:
            raise LLMError("Empty source text")

        last_error = None

        async with self._semaphore:

            for provider in self.providers:

                current_text = chunks[0]

                for attempt in range(self.max_retries):

                    prompt = f"""
You are a data extraction engine.

IMPORTANT RULES:
1. Use ONLY information present in the supplied source text.
2. NEVER invent or hallucinate fields.
3. If a value is unavailable, use null.
4. Preserve the original source URL.
5. Return ONLY valid JSON.
6. Do not add commentary.

SOURCE URL:
{source_url}

EXPECTED SCHEMA:
{schema_description}

SOURCE TEXT:
{current_text}
"""

                    try:
                        result = await self._call_provider(
                            provider,
                            prompt,
                        )

                        data = extract_json(result)

                        data["_llm_provider"] = provider
                        data["_source_url"] = source_url

                        return data

                    except Exception as exc:
                        last_error = exc

                        if self._is_payload_error(exc):
                            # 413/context overflow:
                            # aggressively reduce the current payload.
                            smaller = chunk_text(
                                current_text,
                                max_chars=max(
                                    4000,
                                    len(current_text) // 2,
                                ),
                                overlap=200,
                            )

                            if smaller:
                                current_text = smaller[0]
                                continue

                        if self._is_rate_limit(exc):
                            # Exponential backoff + jitter.
                            delay = min(
                                30,
                                2 ** attempt,
                            ) + random.uniform(0, 1)

                            await asyncio.sleep(delay)
                            continue

                        # Other provider failures move to fallback.
                        break

        raise LLMError(
            f"All LLM providers failed. Last error: {last_error}"
        )


async def extract_with_llm(
    source_text: str,
    source_url: str,
    schema_description: str,
) -> Dict[str, Any]:

    orchestrator = LLMOrchestrator()

    return await orchestrator.extract(
        source_text=source_text,
        source_url=source_url,
        schema_description=schema_description,
    )
