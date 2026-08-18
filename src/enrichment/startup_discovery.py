import asyncio
import aiohttp
import sqlite3
import os
from datetime import datetime, timezone

DB = r".\data\research_papers.db"
TABLE = "startups"

STARTUPS = [
    ("OpenAI", "https://openai.com"),
    ("Anthropic", "https://www.anthropic.com"),
    ("Google DeepMind", "https://deepmind.google"),
    ("Hugging Face", "https://huggingface.co"),
    ("Mistral AI", "https://mistral.ai"),
    ("Cohere", "https://cohere.com"),
    ("Perplexity", "https://www.perplexity.ai"),
    ("Scale AI", "https://scale.com"),
    ("Runway", "https://runwayml.com"),
    ("Character AI", "https://character.ai"),
]

def setup():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS startups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schemaVersion TEXT NOT NULL,
            recordType TEXT NOT NULL,
            source_name TEXT,
            source_url TEXT,
            entityName TEXT NOT NULL,
            employeeCount INTEGER,
            collectedAt TEXT NOT NULL,
            UNIQUE(entityName)
        )
    """)

    conn.commit()
    conn.close()

async def check_url(session, name, url):
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True
        ) as response:
            return response.status
    except Exception:
        return None

async def main():
    print("=" * 70)
    print("STARTUP DISCOVERY")
    print("=" * 70)

    setup()

    connector = aiohttp.TCPConnector(limit=10)

    async with aiohttp.ClientSession(
        connector=connector,
        headers={"User-Agent": "GraphOne-AI-Intelligence/1.0"}
    ) as session:

        results = await asyncio.gather(
            *[
                check_url(session, name, url)
                for name, url in STARTUPS
            ]
        )

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    for (name, url), status in zip(STARTUPS, results):
        if status is not None and status < 500:
            cur.execute("""
                INSERT OR IGNORE INTO startups
                (
                    schemaVersion,
                    recordType,
                    source_name,
                    source_url,
                    entityName,
                    employeeCount,
                    collectedAt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "1.0",
                "STARTUP",
                "Official Website",
                url,
                name,
                None,
                now
            ))

            print(f"[FOUND] {name} | HTTP {status}")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM startups")
    count = cur.fetchone()[0]

    conn.close()

    print()
    print("=" * 70)
    print("STARTUP DISCOVERY COMPLETE")
    print("Total startups:", count)
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
