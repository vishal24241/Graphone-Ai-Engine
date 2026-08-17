import sqlite3
import json
import os
import asyncio

from src.enrichment.github_metrics import fetch_github_stars


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "research_papers.db"
)

JSON_PATH = os.path.join(
    BASE_DIR,
    "data",
    "research_papers.json"
)


# ============================================================
# CREATE / UPDATE DATABASE
# ============================================================

def create_database():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            authors TEXT,

            arxiv_id TEXT UNIQUE,

            paper_url TEXT,

            published_date TEXT,

            huggingface_url TEXT,

            github_url TEXT,

            github_stars INTEGER DEFAULT 0
        )
    """)

    # Add github_stars to an old database
    cursor.execute(
        "PRAGMA table_info(papers)"
    )

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "github_stars" not in columns:

        print("Adding github_stars column...")

        cursor.execute("""
            ALTER TABLE papers
            ADD COLUMN github_stars INTEGER DEFAULT 0
        """)

        print(
            "github_stars column added."
        )

    connection.commit()

    connection.close()

    print(
        "Database created successfully."
    )


# ============================================================
# INSERT / UPDATE PAPERS
# ============================================================

def insert_papers():

    if not os.path.exists(JSON_PATH):

        print(
            f"JSON file not found: {JSON_PATH}"
        )

        return

    with open(
        JSON_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        papers = json.load(file)

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    new_papers = 0
    updated_papers = 0

    for paper in papers:

        try:

            arxiv_id = paper.get(
                "arxiv_id"
            )

            cursor.execute(
                """
                SELECT id
                FROM papers
                WHERE arxiv_id = ?
                """,
                (arxiv_id,)
            )

            existing = cursor.fetchone()

            if existing:

                cursor.execute("""
                    UPDATE papers

                    SET
                        title = ?,
                        authors = ?,
                        paper_url = ?,
                        published_date = ?,
                        huggingface_url = ?,
                        github_url = ?

                    WHERE arxiv_id = ?
                """, (

                    paper.get("title"),

                    json.dumps(
                        paper.get(
                            "authors",
                            []
                        ),
                        ensure_ascii=False
                    ),

                    paper.get(
                        "paper_url"
                    ),

                    paper.get(
                        "published_date"
                    ),

                    paper.get(
                        "huggingface_url"
                    ),

                    paper.get(
                        "github_url"
                    ),

                    arxiv_id
                ))

                updated_papers += 1

            else:

                cursor.execute("""
                    INSERT INTO papers (

                        title,
                        authors,
                        arxiv_id,
                        paper_url,
                        published_date,
                        huggingface_url,
                        github_url,
                        github_stars

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (

                    paper.get("title"),

                    json.dumps(
                        paper.get(
                            "authors",
                            []
                        ),
                        ensure_ascii=False
                    ),

                    arxiv_id,

                    paper.get(
                        "paper_url"
                    ),

                    paper.get(
                        "published_date"
                    ),

                    paper.get(
                        "huggingface_url"
                    ),

                    paper.get(
                        "github_url"
                    ),

                    0
                ))

                new_papers += 1

        except Exception as e:

            print(
                "Insert/update error:",
                e
            )

    connection.commit()

    connection.close()

    print()
    print(
        f"New papers inserted: {new_papers}"
    )

    print(
        f"Existing papers updated: {updated_papers}"
    )


# ============================================================
# UPDATE GITHUB STARS
# ============================================================

async def update_github_stars_async():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            github_url
        FROM papers
        WHERE github_url IS NOT NULL
    """)

    papers = cursor.fetchall()

    print()
    print(
        "Updating GitHub stars..."
    )

    for paper_id, github_url in papers:

        stars = await fetch_github_stars(
            github_url
        )

        cursor.execute("""
            UPDATE papers

            SET github_stars = ?

            WHERE id = ?
        """, (
            stars,
            paper_id
        ))

        print(
            f"ID {paper_id}: "
            f"{github_url} -> "
            f"{stars} stars"
        )

    connection.commit()

    connection.close()


def update_github_stars():

    asyncio.run(
        update_github_stars_async()
    )


# ============================================================
# SHOW PAPERS
# ============================================================

def show_papers():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            title,
            arxiv_id,
            huggingface_url,
            github_url,
            github_stars

        FROM papers

        ORDER BY id
    """)

    papers = cursor.fetchall()

    print()
    print("=" * 90)
    print("PAPERS IN DATABASE")
    print("=" * 90)

    for paper in papers:

        print()
        print("ID:", paper[0])
        print("Title:", paper[1])
        print("arXiv:", paper[2])
        print("HuggingFace:", paper[3])
        print("GitHub:", paper[4])
        print("GitHub Stars:", paper[5])

    print()
    print(
        "Total papers:",
        len(papers)
    )

    connection.close()


# ============================================================
# STATISTICS
# ============================================================

def show_statistics():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM papers"
    )

    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE huggingface_url IS NOT NULL
    """)

    huggingface = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE github_url IS NOT NULL
    """)

    github = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(
            SUM(github_stars),
            0
        )
        FROM papers
    """)

    github_stars = cursor.fetchone()[0]

    print()
    print("=" * 70)
    print("GraphOne Research Database Statistics")
    print("=" * 70)

    print(
        "Total Papers:",
        total
    )

    print(
        "HuggingFace Found:",
        huggingface
    )

    print(
        "GitHub Found:",
        github
    )

    print(
        "Total GitHub Stars:",
        github_stars
    )

    print("=" * 70)

    connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("GraphOne AI Research Database")
    print("=" * 70)

    create_database()

    insert_papers()

    update_github_stars()

    show_papers()

    show_statistics()

    print()
    print(
        "Database setup completed."
    )
