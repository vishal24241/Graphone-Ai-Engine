import asyncio
import aiohttp
import sqlite3
import os
import urllib.parse
from datetime import datetime, timezone

DB = r".\data\research_papers.db"
API = "https://api.github.com"

SEARCH_TERMS = [
    "artificial intelligence",
    "machine learning",
    "generative ai",
    "AI startup",
    "machine learning startup",
    "LLM",
    "deep learning",
    "computer vision",
    "natural language processing",
    "AI agents"
]

MAX_RESULTS = 1000
PER_PAGE = 100
MAX_CONCURRENT = 5

def headers():
    token = os.getenv("GITHUB_TOKEN")

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GraphOne-AI-Research"
    }

def setup_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS startups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schemaVersion TEXT NOT NULL,
            recordType TEXT NOT NULL,
            source_name TEXT,
            source_url TEXT NOT NULL,
            entityName TEXT NOT NULL,
            employeeCount INTEGER,
            description TEXT,
            company_url TEXT,
            location TEXT,
            collectedAt TEXT NOT NULL,
            UNIQUE(entityName)
        )
    """)

    conn.commit()
    conn.close()

async def search_orgs(session, term):
    all_items = []

    for page in range(1, 11):
        query = urllib.parse.quote(
            f'"{term}" type:org'
        )

        url = (
            f"{API}/search/users"
            f"?q={query}"
            f"&per_page={PER_PAGE}"
            f"&page={page}"
        )

        try:
            async with session.get(
                url,
                headers=headers(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                if response.status != 200:
                    print(
                        f"Search error {response.status} "
                        f"for {term}"
                    )
                    break

                data = await response.json()
                items = data.get("items", [])

                if not items:
                    break

                all_items.extend(items)

                print(
                    f"[SEARCH] {term} | "
                    f"page={page} | "
                    f"found={len(items)}"
                )

                await asyncio.sleep(2.2)

        except Exception as e:
            print("Search exception:", e)
            break

    return all_items

async def get_org(session, login):
    url = f"{API}/users/{login}"

    try:
        async with session.get(
            url,
            headers=headers(),
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:

            if response.status != 200:
                return None

            return await response.json()

    except Exception:
        return None

async def main():
    print("=" * 70)
    print("GITHUB STARTUP DISCOVERY")
    print("=" * 70)

    setup_db()

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("ERROR: GITHUB_TOKEN is missing.")
        return

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        candidates = {}

        for term in SEARCH_TERMS:
            items = await search_orgs(session, term)

            for item in items:
                login = item.get("login")

                if login:
                    candidates[login.lower()] = login

                if len(candidates) >= MAX_RESULTS:
                    break

            if len(candidates) >= MAX_RESULTS:
                break

        print()
        print("Unique organization candidates:", len(candidates))

        organizations = []

        for index, login in enumerate(
            list(candidates.values())[:MAX_RESULTS],
            1
        ):
            data = await get_org(session, login)

            if data:
                organizations.append(data)

            if index % 10 == 0:
                print(
                    f"Profiles fetched: "
                    f"{index}/{min(len(candidates), MAX_RESULTS)}"
                )

            await asyncio.sleep(0.2)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    inserted = 0

    for org in organizations:

        login = org.get("login")

        if not login:
            continue

        name = (
            org.get("name")
            or login
        ).strip()

        description = (
            org.get("description")
            or ""
        ).strip()

        company = (
            org.get("company")
            or ""
        ).strip()

        blog = (
            org.get("blog")
            or ""
        ).strip()

        location = (
            org.get("location")
            or ""
        ).strip()

        employee_count = org.get("followers")

        text = (
            f"{name} "
            f"{description} "
            f"{company}"
        ).lower()

        ai_words = [
            "ai",
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "llm",
            "generative",
            "computer vision",
            "nlp",
            "natural language",
            "agent"
        ]

        if not any(word in text for word in ai_words):
            continue

        source_url = (
            f"https://github.com/{login}"
        )

        cur.execute("""
            INSERT OR IGNORE INTO startups
            (
                schemaVersion,
                recordType,
                source_name,
                source_url,
                entityName,
                employeeCount,
                description,
                company_url,
                location,
                collectedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "1.0",
            "STARTUP",
            "GitHub",
            source_url,
            name,
            employee_count,
            description,
            blog,
            location,
            now
        ))

        if cur.rowcount:
            inserted += 1

    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM startups"
    )

    total = cur.fetchone()[0]

    conn.close()

    print()
    print("=" * 70)
    print("STARTUP DISCOVERY COMPLETE")
    print("New startup candidates:", inserted)
    print("Total startup records:", total)
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
