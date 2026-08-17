
import sqlite3
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape

DB = r"./data/signals.db"


def parse_date(value):
    if not value:
        return None

    value = unescape(str(value)).strip()

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


def extract_dates(html):
    patterns = [
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']publishdate["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+itemprop=["\']datePublished["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)'
    ]

    dates = []

    for pattern in patterns:
        for value in re.findall(
            pattern,
            html,
            flags=re.IGNORECASE
        ):
            dt = parse_date(value)

            if dt:
                dates.append(dt)

    return dates


def is_fresh(dt):
    if not dt:
        return False

    now = datetime.now(timezone.utc)

    age = now - dt

    return timedelta(0) <= age <= timedelta(hours=24)


def process_table(conn, table):

    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT id, source_name, source_url, content
        FROM {table}
        """
    )

    rows = cur.fetchall()

    fresh = 0
    dated = 0

    for row_id, source, url, content in rows:

        dates = extract_dates(content or "")

        if not dates:
            continue

        dated += 1

        newest = max(dates)

        if is_fresh(newest):
            fresh += 1

            cur.execute(
                f"""
                UPDATE {table}
                SET published_date = ?
                WHERE id = ?
                """,
                (
                    newest.isoformat(),
                    row_id
                )
            )

    conn.commit()

    return len(rows), dated, fresh


def main():

    print("=" * 70)
    print("24-HOUR FRESHNESS PARSER")
    print("=" * 70)

    conn = sqlite3.connect(DB)

    news_total, news_dated, news_fresh = process_table(
        conn,
        "news"
    )

    jobs_total, jobs_dated, jobs_fresh = process_table(
        conn,
        "jobs"
    )

    print()
    print("NEWS")
    print("Source snapshots:", news_total)
    print("With detected dates:", news_dated)
    print("Fresh within 24h:", news_fresh)

    print()
    print("JOBS")
    print("Source snapshots:", jobs_total)
    print("With detected dates:", jobs_dated)
    print("Fresh within 24h:", jobs_fresh)

    conn.close()

    print()
    print("=" * 70)
    print("FRESHNESS PARSING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
