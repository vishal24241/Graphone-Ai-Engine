import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timezone

DB = r".\data\research_papers.db"

URLS = [
    "https://www.ycombinator.com/companies",
]

async def fetch(session, url):
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=30),
            allow_redirects=True
        ) as r:
            text = await r.text()
            print("YC status:", r.status)
            print("Response length:", len(text))
            return text
    except Exception as e:
        print("Fetch error:", e)
        return ""

async def main():
    print("=" * 70)
    print("STARTUP BULK SOURCE TEST")
    print("=" * 70)

    async with aiohttp.ClientSession(
        headers={
            "User-Agent":
            "Mozilla/5.0 GraphOne-AI-Research"
        }
    ) as session:
        html = await fetch(session, URLS[0])

    if not html:
        print("No data received.")
        return

    print("YC page fetched successfully.")
    print("Next step: parse company records.")

if __name__ == "__main__":
    asyncio.run(main())
