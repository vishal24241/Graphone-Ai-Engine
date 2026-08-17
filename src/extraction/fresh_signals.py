
import asyncio
import aiohttp
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

DB = r"./data/signals.db"

NEWS_SOURCES = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/",
    "The Decoder": "https://the-decoder.com/",
    "AI News": "https://www.artificialintelligence-news.com/",
    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/"
}

JOB_SOURCES = {
    "RemoteOK AI": "https://remoteok.com/remote-ai-jobs",
    "We Work Remotely": "https://weworkremotely.com/remote-jobs/search?term=ai",
    "Wellfound AI": "https://wellfound.com/jobs",
    "AI Jobs": "https://ai-jobs.net/",
    "Indeed AI": "https://www.indeed.com/jobs?q=artificial+intelligence"
}


def now_utc():
    return datetime.now(timezone.utc)


def parse_date(value):
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    try:
        value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def within_24_hours(dt):
    if not dt:
        return False

    age = now_utc() - dt

    return timedelta(0) <= age <= timedelta(hours=24)


def make_id(source, url):
    return hashlib.sha256(
        f"{source}|{url}".encode()
    ).hexdigest()


async def fetch(session, source, url):
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=30),
            allow_redirects=True
        ) as response:

            text = await response.text(errors="ignore")

            print(
                f"[FETCH] {source} | "
                f"HTTP {response.status} | "
                f"{len(text)} bytes"
            )

            return response.status, text

    except Exception as e:
        print(f"[ERROR] {source}: {e}")
        return 0, ""


async def main():

    print("=" * 70)
    print("FRESH AI SIGNAL INGESTION")
    print("=" * 70)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/151 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml"
    }

    async with aiohttp.ClientSession(
        headers=headers
    ) as session:

        news_results = []

        for source, url in NEWS_SOURCES.items():

            status, text = await fetch(
                session,
                source,
                url
            )

            if status == 200:
                news_results.append(
                    (source, url, text)
                )

            await asyncio.sleep(1)

        job_results = []

        for source, url in JOB_SOURCES.items():

            status, text = await fetch(
                session,
                source,
                url
            )

            if status == 200:
                job_results.append(
                    (source, url, text)
                )

            await asyncio.sleep(1)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id TEXT PRIMARY KEY,
            schema_version TEXT,
            record_type TEXT,
            source_name TEXT,
            source_url TEXT,
            title TEXT,
            content TEXT,
            published_date TEXT,
            collected_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            schema_version TEXT,
            record_type TEXT,
            source_name TEXT,
            source_url TEXT,
            company TEXT,
            title TEXT,
            content TEXT,
            published_date TEXT,
            is_remote INTEGER,
            role_family TEXT,
            collected_at TEXT
        )
    """)

    collected = now_utc().isoformat()

    # Store raw source snapshots.
    # Actual article/job dates are extracted in the parser stage.
    for source, url, text in news_results:

        record_id = make_id(source, url)

        cur.execute("""
            INSERT OR REPLACE INTO news
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            "1.0",
            "NEWS",
            source,
            url,
            "",
            text[:100000],
            None,
            collected
        ))

    for source, url, text in job_results:

        record_id = make_id(source, url)

        cur.execute("""
            INSERT OR REPLACE INTO jobs
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            "1.0",
            "JOB",
            source,
            url,
            "",
            "",
            text[:100000],
            None,
            0,
            "Engineering",
            collected
        ))

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM news")
    news_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM jobs")
    job_count = cur.fetchone()[0]

    conn.close()

    print()
    print("=" * 70)
    print("FRESH SIGNAL INGESTION COMPLETE")
    print("News source snapshots:", news_count)
    print("Job source snapshots:", job_count)
    print("Database:", DB)
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
