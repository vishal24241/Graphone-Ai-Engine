import asyncio
import sqlite3
import os

import aiohttp

from enrichment.github_metrics import fetch_github_stars


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

CONCURRENCY = 5


async def enrich_github():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            github_url,
            github_stars
        FROM papers
        WHERE github_url IS NOT NULL
        AND github_url != ''
    """)

    papers = cursor.fetchall()

    print()
    print("=" * 70)
    print("GITHUB ENRICHMENT")
    print("=" * 70)
    print("Database:", DATABASE_PATH)
    print("GitHub papers:", len(papers))
    print("=" * 70)

    if not papers:

        print("No GitHub repositories found.")

        connection.close()

        return

    semaphore = asyncio.Semaphore(
        CONCURRENCY
    )

    async with aiohttp.ClientSession() as session:

        async def process(paper):

            async with semaphore:

                stars = await fetch_github_stars(
                    paper["github_url"],
                    session
                )

                return (
                    paper["id"],
                    stars
                )

        tasks = [
            process(paper)
            for paper in papers
        ]

        results = await asyncio.gather(
            *tasks
        )

    updated = 0
    total_stars = 0

    for paper_id, stars in results:

        cursor.execute("""
            UPDATE papers
            SET github_stars = ?
            WHERE id = ?
        """, (
            stars,
            paper_id
        ))

        updated += 1
        total_stars += stars

    connection.commit()

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE github_url IS NOT NULL
        AND github_url != ''
    """)

    github_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE github_url IS NOT NULL
        AND github_url != ''
        AND github_stars > 0
    """)

    starred_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(
            SUM(github_stars),
            0
        )
        FROM papers
    """)

    database_total_stars = cursor.fetchone()[0]

    connection.close()

    print()
    print("=" * 70)
    print("GITHUB ENRICHMENT COMPLETE")
    print("=" * 70)
    print("GitHub papers:", github_count)
    print("Papers processed:", updated)
    print("Papers with stars:", starred_count)
    print("Stars from this run:", total_stars)
    print("Database total stars:", database_total_stars)
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(
        enrich_github()
    )
