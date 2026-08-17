from pathlib import Path
from fastapi import FastAPI, HTTPException
import sqlite3
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# CONFIG
# ============================================================

DATABASE = str(Path(__file__).resolve().parents[2] / "data" / "research_papers.db")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="GraphOne AI Research API",
    description="API for AI research papers",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "GraphOne AI Research API is running",
        "version": "1.0.0"
    }


# ============================================================
# GET ALL PAPERS
# ============================================================

@app.get("/papers")
def get_papers():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM papers
        ORDER BY id DESC
    """)

    papers = cursor.fetchall()

    connection.close()

    return {
        "total": len(papers),
        "papers": [
            dict(paper)
            for paper in papers
        ]
    }


# ============================================================
# GET SINGLE PAPER
# ============================================================

@app.get("/papers/{paper_id}")
def get_paper(paper_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM papers
        WHERE id = ?
        """,
        (paper_id,)
    )

    paper = cursor.fetchone()

    connection.close()

    if paper is None:

        raise HTTPException(
            status_code=404,
            detail="Paper not found"
        )

    return dict(paper)


# ============================================================
# SEARCH PAPERS
# ============================================================

@app.get("/search")
def search_papers(q: str):

    connection = get_connection()

    cursor = connection.cursor()

    search_term = f"%{q}%"

    cursor.execute(
        """
        SELECT *
        FROM papers
        WHERE
            title LIKE ?
            OR authors LIKE ?
            OR arxiv_id LIKE ?
        ORDER BY id DESC
        """,
        (
            search_term,
            search_term,
            search_term
        )
    )

    papers = cursor.fetchall()

    connection.close()

    return {
        "query": q,
        "total": len(papers),
        "papers": [
            dict(paper)
            for paper in papers
        ]
    }


# ============================================================
# STATISTICS
# ============================================================

# ============================================================
# DATASET COUNTS
# ============================================================

@app.get("/datasets")
def get_datasets():
    import sqlite3

    base = Path(__file__).resolve().parents[2] / "data"

    def count_rows(db, table):
        try:
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            count = cur.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    return {
        "papers": count_rows(base / "research_papers.db", "papers"),
        "startups": count_rows(base / "startups.db", "startups"),
        "products": count_rows(base / "products.db", "products"),
        "signals": {
            "news": count_rows(base / "signals.db", "news"),
            "jobs": count_rows(base / "signals.db", "jobs")
        }
    }


# ============================================================
# PRODUCTS
# ============================================================

@app.get("/products")
def get_products(limit: int = 100):
    import sqlite3

    limit = max(1, min(limit, 1000))

    db = Path(__file__).resolve().parents[2] / "data" / "products.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM products LIMIT ?",
        (limit,)
    ).fetchall()

    conn.close()

    return {
        "total_returned": len(rows),
        "products": [dict(row) for row in rows]
    }


# ============================================================
# STARTUPS
# ============================================================

@app.get("/startups")
def get_startups(limit: int = 100):
    import sqlite3

    limit = max(1, min(limit, 1000))

    db = Path(__file__).resolve().parents[2] / "data" / "startups.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM startups LIMIT ?",
        (limit,)
    ).fetchall()

    conn.close()

    return {
        "total_returned": len(rows),
        "startups": [dict(row) for row in rows]
    }


# ============================================================
# SIGNALS
# ============================================================

@app.get("/signals")
def get_signals(limit: int = 100):
    import sqlite3

    limit = max(1, min(limit, 1000))

    db = Path(__file__).resolve().parents[2] / "data" / "signals.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]

    result = {}

    for table in tables:
        rows = conn.execute(
            f"SELECT * FROM [{table}] LIMIT ?",
            (limit,)
        ).fetchall()

        result[table] = [dict(row) for row in rows]

    conn.close()

    return result


@app.get("/stats")
def get_stats():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM papers"
    )

    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM papers
        WHERE huggingface_url IS NOT NULL
        """
    )

    huggingface = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM papers
        WHERE github_url IS NOT NULL
        """
    )

    github = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COALESCE(SUM(github_stars), 0)
        FROM papers
        """
    )

    github_stars = cursor.fetchone()[0]

    connection.close()

    return {
        "total_papers": total,
        "huggingface_found": huggingface,
        "github_found": github,
        "total_github_stars": github_stars
    }
