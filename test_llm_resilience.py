import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from src.llm.orchestrator import (
    LLMOrchestrator,
    chunk_text,
    extract_json,
)


async def main():

    print("=" * 70)
    print("GRAPHONE LLM RESILIENCE TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. CHUNKING TEST
    # ---------------------------------------------------------
    print("\n[1] CHUNKING TEST")

    text = "Artificial intelligence research paper content. " * 5000

    chunks = chunk_text(
        text,
        max_chars=4000,
        overlap=200,
    )

    print("Original chars:", len(text))
    print("Chunks:", len(chunks))
    print("Largest chunk:", max(len(x) for x in chunks))

    assert len(chunks) > 1
    assert max(len(x) for x in chunks) <= 4000

    print("CHUNKING: PASS")


    # ---------------------------------------------------------
    # 2. JSON EXTRACTION TEST
    # ---------------------------------------------------------
    print("\n[2] JSON EXTRACTION TEST")

    raw = """
    ```json
    {
        "recordType": "RESEARCH_PAPER",
        "title": "Test Paper",
        "github_url": null
    }
    ```
    """

    data = extract_json(raw)

    assert data["recordType"] == "RESEARCH_PAPER"
    assert data["title"] == "Test Paper"

    print("JSON EXTRACTION: PASS")


    # ---------------------------------------------------------
    # 3. ERROR CLASSIFICATION
    # ---------------------------------------------------------
    print("\n[3] ERROR CLASSIFICATION TEST")

    orchestrator = LLMOrchestrator()

    assert orchestrator._is_rate_limit(
        Exception("429 Too Many Requests")
    )

    assert orchestrator._is_rate_limit(
        Exception("rate limit exceeded")
    )

    assert orchestrator._is_payload_error(
        Exception("413 Payload Too Large")
    )

    assert orchestrator._is_payload_error(
        Exception("context window exceeded")
    )

    print("429 DETECTION: PASS")
    print("413 DETECTION: PASS")


    # ---------------------------------------------------------
    # 4. PROVIDER ORDER
    # ---------------------------------------------------------
    print("\n[4] FALLBACK ORDER TEST")

    expected = [
        "gemini",
        "groq",
        "deepseek",
    ]

    assert orchestrator.providers == expected

    print("Fallback chain:")
    print("  1. Gemini")
    print("  2. Groq")
    print("  3. DeepSeek")
    print("FALLBACK ORDER: PASS")


    # ---------------------------------------------------------
    # 5. CONFIG TEST
    # ---------------------------------------------------------
    print("\n[5] CONFIGURATION TEST")

    print("Max retries:", orchestrator.max_retries)
    print("Timeout:", orchestrator.timeout)

    assert orchestrator.max_retries >= 1
    assert orchestrator.timeout >= 1

    print("CONFIGURATION: PASS")


    print("\n" + "=" * 70)
    print("ALL LLM RESILIENCE TESTS PASSED")
    print("=" * 70)


asyncio.run(main())
