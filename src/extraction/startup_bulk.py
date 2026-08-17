import os
import asyncio
import aiohttp
import sqlite3
import json
from datetime import datetime, timezone

DB = r".\data\startups.db"
API = "https://api.github.com/search/users"

MAX_PAGES = 10
PER_PAGE = 100

async def fetch_page(session, page):
    params = {
        "q": "type:org",
        "per_page": PER_PAGE,
        "page": page
    }

    async with session.get(API, params=params, timeout=30) as r:
        print(f"[SEARCH] organizations | page={page} | status={r.status}")

        if r.status != 200:
            print("ERROR:", await r.text())
            return []

        data = await r.json()
        return data.get("items", [])


async def main():

    print("=" * 70)
    print("STARTUP BULK EXTRACTION")
    print("=" * 70)

    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GraphOne-AI-Startup-Discovery",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_items = []

    async with aiohttp.ClientSession(headers=headers) as session:

        for page in range(1, MAX_PAGES + 1):

            items = await fetch_page(session, page)

            all_items.extend(items)

            print(
                f"[FOUND] page={page} "
                f"records={len(items)} "
                f"total={len(all_items)}"
            )

            if len(items) < PER_PAGE:
                break

            await asyncio.sleep(1)

    # Remove duplicate organizations
    unique = {}

    for item in all_items:
        login = item.get("login")

        if login:
            unique[login.lower()] = item

    records = list(unique.values())[:1000]

    os.makedirs(os.path.dirname(DB), exist_ok=True)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS startups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schema_version TEXT,
            record_type TEXT,
            source_name TEXT,
            source_url TEXT,
            entity_name TEXT,
            employee_count INTEGER,
            collected_at TEXT,
            raw_data TEXT
        )
    """)

    cur.execute("DELETE FROM startups")

    now = datetime.now(timezone.utc).isoformat()

    for item in records:

        name = item.get("login")

        source_url = item.get(
            "html_url",
            ""
        )

        cur.execute("""
            INSERT INTO startups (
                schema_version,
                record_type,
                source_name,
                source_url,
                entity_name,
                employee_count,
                collected_at,
                raw_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "1.0",
            "STARTUP",
            "GitHub",
            source_url,
            name,
            None,
            now,
            json.dumps(item)
        ))

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM startups")

    count = cur.fetchone()[0]

    conn.close()

    print()
    print("=" * 70)
    print("STARTUP BULK EXTRACTION COMPLETE")
    print("Unique startups:", count)
    print("Database:", DB)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
