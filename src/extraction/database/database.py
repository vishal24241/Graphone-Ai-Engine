import json
import sqlite3
import os


# ============================================================
# CONFIG
# ============================================================

JSON_FILE = "data/research_papers.json"
DATABASE_FILE = "data/research_papers.db"


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    os.makedirs(
        "data",
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_FILE
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

            github_url TEXT

        )
    """)

    connection.commit()

    return connection


# ============================================================
# LOAD JSON
# ============================================================

def load_json():

    if not os.path.exists(JSON_FILE):

        raise FileNotFoundError(
            f"JSON file not found: {JSON_FILE}"
        )

    with open(
        JSON_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# INSERT PAPERS
# ============================================================

def insert_papers(
    connection,
    papers
):

    cursor = connection.cursor()

    for paper in papers:

        authors = ", ".join(
            paper.get(
                "authors",
                []
            )
        )

        cursor.execute("""
            INSERT OR REPLACE INTO papers (

                title,
                authors,
                arxiv_id,
                paper_url,
                published_date,
                huggingface_url,
                github_url

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            paper.get("title"),

            authors,

            paper.get("arxiv_id"),

            paper.get("paper_url"),

            paper.get("published_date"),

            paper.get("huggingface_url"),

            paper.get("github_url")

        ))

    connection.commit()


# ============================================================
# SHOW STATISTICS
# ============================================================

def show_statistics(
    connection
):

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

    print()
    print("=" * 60)
    print("GraphOne Database Statistics")
    print("=" * 60)

    print(
        "Total Papers:",
        total
    )

    print(
        "HuggingFace:",
        huggingface
    )

    print(
        "GitHub:",
        github
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("GraphOne AI Database")
    print("=" * 60)

    papers = load_json()

    print(
        f"Loaded {len(papers)} papers from JSON"
    )

    connection = create_database()

    insert_papers(
        connection,
        papers
    )

    print(
        "Papers inserted into SQLite database."
    )

    show_statistics(
        connection
    )

    connection.close()

    print()
    print(
        "Database created:",
        DATABASE_FILE
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()