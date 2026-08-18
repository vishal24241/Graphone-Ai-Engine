import sqlite3
import json
import os
from datetime import datetime, timezone


# ============================================================
# CONFIG
# ============================================================

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

JSON_PATH = os.path.join(
    BASE_DIR,
    "data",
    "research_papers.json"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    connection = get_connection()

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

            github_stars INTEGER DEFAULT 0,

            collected_at TEXT
        )
    """)

    # --------------------------------------------------------
    # Migration for existing database
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(papers)"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]

    if "github_stars" not in columns:

        print(
            "Adding github_stars column..."
        )

        cursor.execute("""
            ALTER TABLE papers
            ADD COLUMN github_stars INTEGER DEFAULT 0
        """)

        print(
            "github_stars column added."
        )

    if "collected_at" not in columns:

        print(
            "Adding collected_at column..."
        )

        cursor.execute("""
            ALTER TABLE papers
            ADD COLUMN collected_at TEXT
        """)

        print(
            "collected_at column added."
        )

    # --------------------------------------------------------
    # Indexes
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_papers_arxiv_id
        ON papers(arxiv_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_papers_title
        ON papers(title)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_papers_published_date
        ON papers(published_date)
    """)

    connection.commit()

    connection.close()

    print(
        "Database created successfully."
    )

    print(
        "Database path:",
        DATABASE_PATH
    )


# ============================================================
# LOAD JSON
# ============================================================

def load_papers():

    if not os.path.exists(JSON_PATH):

        print(
            "research_papers.json not found:"
        )

        print(
            JSON_PATH
        )

        return []

    try:

        with open(
            JSON_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            papers = json.load(file)

        if not isinstance(
            papers,
            list
        ):

            print(
                "Invalid JSON format."
            )

            return []

        return papers

    except json.JSONDecodeError as e:

        print(
            "JSON decode error:",
            e
        )

        return []

    except Exception as e:

        print(
            "Error loading JSON:",
            e
        )

        return []


# ============================================================
# INSERT / UPDATE PAPERS
# ============================================================

def insert_papers():

    papers = load_papers()

    if not papers:

        print(
            "No papers found in JSON."
        )

        return

    connection = get_connection()

    cursor = connection.cursor()

    new_papers = 0
    updated_papers = 0
    failed_papers = 0

    collected_at = datetime.now(
        timezone.utc
    ).isoformat()

    for paper in papers:

        try:

            title = paper.get(
                "title"
            )

            arxiv_id = paper.get(
                "arxiv_id"
            )

            if not title:

                print(
                    "Skipping paper without title."
                )

                failed_papers += 1

                continue

            # ------------------------------------------------
            # Authors
            # ------------------------------------------------

            authors = paper.get(
                "authors",
                []
            )

            if isinstance(
                authors,
                list
            ):

                authors_json = json.dumps(
                    authors,
                    ensure_ascii=False
                )

            else:

                authors_json = json.dumps(
                    [str(authors)],
                    ensure_ascii=False
                )

            # ------------------------------------------------
            # GitHub Stars
            # ------------------------------------------------

            github_stars = paper.get(
                "github_stars",
                0
            )

            if github_stars is None:

                github_stars = 0

            try:

                github_stars = int(
                    github_stars
                )

            except (
                ValueError,
                TypeError
            ):

                github_stars = 0

            # ------------------------------------------------
            # Check existing paper
            # ------------------------------------------------

            existing = None

            if arxiv_id:

                cursor.execute("""
                    SELECT id
                    FROM papers
                    WHERE arxiv_id = ?
                """, (
                    arxiv_id,
                ))

                existing = cursor.fetchone()

            # ------------------------------------------------
            # UPDATE existing
            # ------------------------------------------------

            if existing:

                cursor.execute("""
                    UPDATE papers
                    SET

                        title = ?,

                        authors = ?,

                        paper_url = ?,

                        published_date = ?,

                        huggingface_url = ?,

                        github_url = ?,

                        github_stars = ?,

                        collected_at = ?

                    WHERE arxiv_id = ?

                """, (

                    title,

                    authors_json,

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

                    github_stars,

                    collected_at,

                    arxiv_id
                ))

                updated_papers += 1

            # ------------------------------------------------
            # INSERT new
            # ------------------------------------------------

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

                        github_stars,

                        collected_at

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    title,

                    authors_json,

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

                    github_stars,

                    collected_at

                ))

                new_papers += 1

        except Exception as e:

            failed_papers += 1

            print(
                "Insert error:",
                e
            )

    connection.commit()

    connection.close()

    print()
    print(
        "=" * 80
    )

    print(
        "DATABASE INGESTION"
    )

    print(
        "=" * 80
    )

    print(
        "New papers:",
        new_papers
    )

    print(
        "Updated papers:",
        updated_papers
    )

    print(
        "Failed papers:",
        failed_papers
    )

    print(
        "Total processed:",
        len(papers)
    )

    print(
        "=" * 80
    )


# ============================================================
# SHOW PAPERS
# ============================================================

def show_papers():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            title,

            arxiv_id,

            huggingface_url,

            github_url,

            github_stars,

            published_date

        FROM papers

        ORDER BY id ASC
    """)

    papers = cursor.fetchall()

    print()
    print(
        "=" * 100
    )

    print(
        "PAPERS IN DATABASE"
    )

    print(
        "=" * 100
    )

    for paper in papers:

        print()

        print(
            "ID:",
            paper["id"]
        )

        print(
            "Title:",
            paper["title"]
        )

        print(
            "arXiv:",
            paper["arxiv_id"]
        )

        print(
            "Published:",
            paper["published_date"]
        )

        print(
            "HuggingFace:",
            paper["huggingface_url"]
        )

        print(
            "GitHub:",
            paper["github_url"]
        )

        print(
            "GitHub Stars:",
            paper["github_stars"]
        )

    print()

    print(
        "Total papers:",
        len(papers)
    )

    connection.close()


# ============================================================
# SHOW STATISTICS
# ============================================================

def show_statistics():

    connection = get_connection()

    cursor = connection.cursor()

    # Total papers

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
    """)

    total = cursor.fetchone()[0]

    # HuggingFace

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE huggingface_url IS NOT NULL
        AND huggingface_url != ''
    """)

    huggingface = cursor.fetchone()[0]

    # GitHub

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE github_url IS NOT NULL
        AND github_url != ''
    """)

    github = cursor.fetchone()[0]

    # GitHub stars

    cursor.execute("""
        SELECT COALESCE(
            SUM(github_stars),
            0
        )
        FROM papers
    """)

    github_stars = cursor.fetchone()[0]

    # Papers with actual stars

    cursor.execute("""
        SELECT COUNT(*)
        FROM papers
        WHERE github_stars > 0
    """)

    papers_with_stars = cursor.fetchone()[0]

    print()

    print(
        "=" * 80
    )

    print(
        "GraphOne Research Database Statistics"
    )

    print(
        "=" * 80
    )

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
        "Papers With GitHub Stars:",
        papers_with_stars
    )

    print(
        "Total GitHub Stars:",
        github_stars
    )

    print(
        "=" * 80
    )

    connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 80
    )

    print(
        "GraphOne AI Research Database"
    )

    print(
        "=" * 80
    )

    create_database()

    insert_papers()

    show_papers()

    show_statistics()

    print()

    print(
        "Database setup completed."
    )

    print(
        "Database:",
        DATABASE_PATH
    )