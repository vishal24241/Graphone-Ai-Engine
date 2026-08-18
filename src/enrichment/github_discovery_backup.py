import asyncio
import os
import random
import sqlite3
from urllib.parse import quote

import aiohttp


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "research_papers.db"
)

GITHUB_API = "https://api.github.com"

MAX_CONCURRENT = 5
MAX_RETRIES = 5
BASE_DELAY = 2

# GitHub Search API: keep requests below 30/minute
SEARCH_MIN_INTERVAL = 2.2
_search_rate_lock = asyncio.Lock()
_last_search_time = 0.0


def github_headers():
    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GraphOne-AI-Engine"
    }

    if token and token != "YOUR_GITHUB_TOKEN":
        headers["Authorization"] = f"Bearer {token}"

    return headers


def normalize_repo_url(url):
    if not url:
        return None

    url = url.rstrip("/")

    if url.endswith(".git"):
        url = url[:-4]

    return url


async def github_search(
    session,
    semaphore,
    title
):
    query = quote(
        f'"{title}" in:name,description,readme'
    )

    url = (
        f"{GITHUB_API}/search/repositories"
        f"?q={query}&per_page=5"
    )

    async with semaphore:

        for attempt in range(MAX_RETRIES):

            try:

                global _last_search_time

                async with _search_rate_lock:
                    now = asyncio.get_running_loop().time()
                    wait = SEARCH_MIN_INTERVAL - (
                        now - _last_search_time
                    )

                    if wait > 0:
                        await asyncio.sleep(wait)

                    _last_search_time = (
                        asyncio.get_running_loop().time()
                    )

                async with session.get(
                    url,
                    headers=github_headers(),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status == 200:

                        data = await response.json()

                        items = data.get(
                            "items",
                            []
                        )

                        if not items:
                            return None

                        best = None
                        best_score = 0

                        title_words = set(
                            title.lower().split()
                        )

                        for repo in items:

                            repo_text = (
                                (repo.get("name") or "") + " " + (repo.get("description") or "")
                            ).lower()

                            matches = sum(
                                1
                                for word in title_words
                                if len(word) > 3
                                and word in repo_text
                            )

                            score = (
                                matches / max(
                                    len(title_words),
                                    1
                                )
                            )

                            if score > best_score:

                                best_score = score

                                best = {
                                    "url": normalize_repo_url(
                                        repo.get("html_url")
                                    ),
                                    "stars": repo.get(
                                        "stargazers_count",
                                        0
                                    ),
                                    "score": round(
                                        score,
                                        3
                                    )
                                }

                        if best and best_score >= 0.5:
                            return best

                        return None

                    if response.status in (403, 429):

                        retry_after = response.headers.get(
                            "Retry-After"
                        )

                        remaining = response.headers.get(
                            "X-RateLimit-Remaining"
                        )

                        reset = response.headers.get(
                            "X-RateLimit-Reset"
                        )

                        if retry_after:

                            try:
                                delay = float(
                                    retry_after
                                )
                            except ValueError:
                                delay = BASE_DELAY * (
                                    2 ** attempt
                                )

                        elif remaining == "0" and reset:

                            import time

                            delay = max(
                                1,
                                int(reset)
                                - int(time.time())
                                + 1
                            )

                        else:

                            delay = (
                                BASE_DELAY
                                * (2 ** attempt)
                                + random.uniform(0, 1)
                            )

                        if attempt == MAX_RETRIES - 1:

                            print(
                                f"GitHub rate limit "
                                f"after {MAX_RETRIES} attempts: "
                                f"{title[:60]}"
                            )

                            return None

                        print(
                            f"GitHub {response.status}. "
                            f"Retrying in "
                            f"{delay:.1f}s..."
                        )

                        await asyncio.sleep(
                            delay
                        )

                        continue

                    if response.status >= 500:

                        delay = (
                            BASE_DELAY
                            * (2 ** attempt)
                            + random.uniform(0, 1)
                        )

                        if attempt < MAX_RETRIES - 1:

                            print(
                                f"GitHub server error "
                                f"{response.status}. "
                                f"Retrying in "
                                f"{delay:.1f}s..."
                            )

                            await asyncio.sleep(
                                delay
                            )

                            continue

                        return None

                    print(
                        f"GitHub search status: "
                        f"{response.status}"
                    )

                    return None

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError
            ) as e:

                delay = (
                    BASE_DELAY
                    * (2 ** attempt)
                    + random.uniform(0, 1)
                )

                if attempt < MAX_RETRIES - 1:

                    print(
                        f"GitHub request error: {e}. "
                        f"Retrying in "
                        f"{delay:.1f}s..."
                    )

                    await asyncio.sleep(
                        delay
                    )

                else:

                    print(
                        f"GitHub request failed: {e}"
                    )

            except Exception as e:

                print(
                    f"GitHub API error: {e}"
                )

                return None

    return None


async def main():

    print()
    print("=" * 70)
    print("GITHUB DISCOVERY")
    print("=" * 70)
    print("Database:", DATABASE_PATH)

    if not os.path.exists(DATABASE_PATH):

        print("Database not found.")
        return

    token = os.getenv("GITHUB_TOKEN")

    if not token or token == "YOUR_GITHUB_TOKEN":

        print(
            "WARNING: GITHUB_TOKEN is not set."
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            title
        FROM papers
        WHERE
            github_url IS NULL
            OR github_url = ''
        ORDER BY id
    """)

    papers = cursor.fetchall()

    connection.close()

    print(
        "Papers requiring GitHub discovery:",
        len(papers)
    )

    if not papers:

        print("Nothing to discover.")
        return

    semaphore = asyncio.Semaphore(
        MAX_CONCURRENT
    )

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        async def process(paper):

            result = await github_search(
                session,
                semaphore,
                paper["title"]
            )

            return (
                paper["id"],
                paper["title"],
                result
            )

        results = await asyncio.gather(
            *[
                process(paper)
                for paper in papers
            ]
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    found = 0
    skipped = 0
    stars_added = 0

    for paper_id, title, result in results:

        if result:

            cursor.execute("""
                UPDATE papers
                SET
                    github_url = ?,
                    github_stars = ?
                WHERE id = ?
            """, (
                result["url"],
                result["stars"],
                paper_id
            ))

            found += 1
            stars_added += result["stars"]

            print(
                f"[FOUND] {title[:65]}"
            )

            print(
                f"        {result['url']}"
            )

            print(
                f"        score={result['score']} "
                f"stars={result['stars']}"
            )

        else:

            skipped += 1

    connection.commit()

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE github_url IS NOT NULL
        AND github_url != ''
    """)

    github_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(
            SUM(github_stars),
            0
        )
        FROM papers
    """)

    total_stars = cursor.fetchone()[0]

    connection.close()

    print()
    print("=" * 70)
    print("GITHUB DISCOVERY COMPLETE")
    print("=" * 70)
    print("New repositories found:", found)
    print("No match:", skipped)
    print("Total GitHub papers:", github_count)
    print("Stars from new matches:", stars_added)
    print("Total GitHub stars:", total_stars)
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(main())

