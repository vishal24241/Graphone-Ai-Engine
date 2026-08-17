import os
import asyncio
import aiohttp
import sqlite3
import json
from datetime import datetime, timezone

DB = r".\data\products.db"
API = "https://api.github.com/search/repositories"

QUERIES = [
    "topic:artificial-intelligence",
    "topic:machine-learning",
    "topic:generative-ai",
    "topic:llm",
    "topic:computer-vision",
    "topic:nlp",
    "topic:deep-learning",
    "topic:ai"
]

PER_PAGE = 100
MAX_PAGES = 2


async def fetch(session, query, page):

    params = {
        "q": query,
        "per_page": PER_PAGE,
        "page": page,
        "sort": "stars",
        "order": "desc"
    }

    async with session.get(
        API,
        params=params,
        timeout=30
    ) as response:

        print(
            f"[SEARCH] {query} | "
            f"page={page} | "
            f"status={response.status}"
        )

        if response.status != 200:
            print(await response.text())
            return []

        data = await response.json()

        return data.get("items", [])


async def main():

    print("=" * 70)
    print("PRODUCT BULK EXTRACTION")
    print("=" * 70)

    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GraphOne-AI-Product-Discovery",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    products = {}

    async with aiohttp.ClientSession(
        headers=headers
    ) as session:

        for query in QUERIES:

            for page in range(1, MAX_PAGES + 1):

                items = await fetch(
                    session,
                    query,
                    page
                )

                for item in items:

                    repo_id = item.get("id")

                    if repo_id:
                        products[repo_id] = item

                print(
                    f"[FOUND] "
                    f"{len(items)} records | "
                    f"unique={len(products)}"
                )

                if len(items) < PER_PAGE:
                    break

                await asyncio.sleep(1)

                if len(products) >= 1000:
                    break

            if len(products) >= 1000:
                break

    records = list(products.values())[:1000]

    os.makedirs(
        os.path.dirname(DB),
        exist_ok=True
    )

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schema_version TEXT,
            record_type TEXT,
            source_name TEXT,
            source_url TEXT,
            startup_name TEXT,
            product_name TEXT,
            pricing_model TEXT,
            collected_at TEXT,
            raw_data TEXT
        )
    """)

    cur.execute("DELETE FROM products")

    now = datetime.now(
        timezone.utc
    ).isoformat()

    for item in records:

        owner = (
            item.get("owner") or {}
        ).get("login", "")

        product_name = item.get(
            "name",
            ""
        )

        source_url = item.get(
            "html_url",
            ""
        )

        cur.execute("""
            INSERT INTO products (
                schema_version,
                record_type,
                source_name,
                source_url,
                startup_name,
                product_name,
                pricing_model,
                collected_at,
                raw_data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "1.0",
            "PRODUCT",
            "GitHub",
            source_url,
            owner,
            product_name,
            "UNKNOWN",
            now,
            json.dumps(item)
        ))

    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM products"
    )

    count = cur.fetchone()[0]

    conn.close()

    print()
    print("=" * 70)
    print("PRODUCT BULK EXTRACTION COMPLETE")
    print("Unique products:", count)
    print("Database:", DB)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
