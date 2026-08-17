import sqlite3
import json
import csv
from pathlib import Path

from src.entity_resolution.resolver import EntityResolver

resolver = EntityResolver()

output = Path("./data/entity_mapping_log.csv")

rows = []

# -----------------------------
# STARTUPS
# -----------------------------
conn = sqlite3.connect("./data/startups.db")
conn.row_factory = sqlite3.Row

for row in conn.execute("""
    SELECT entity_name, source_url
    FROM startups
"""):
    raw = row["entity_name"] or ""
    result = resolver.resolve_record(
        raw_name=raw,
        entity_type="STARTUP",
        source_url=row["source_url"] or "",
    )

    rows.append(result)

conn.close()


# -----------------------------
# PRODUCTS
# -----------------------------
conn = sqlite3.connect("./data/products.db")
conn.row_factory = sqlite3.Row

for row in conn.execute("""
    SELECT startup_name, product_name, source_url
    FROM products
"""):
    raw = row["product_name"] or ""

    result = resolver.resolve_record(
        raw_name=raw,
        entity_type="PRODUCT",
        source_url=row["source_url"] or "",
    )

    result["startup_name"] = row["startup_name"] or ""

    rows.append(result)

conn.close()


# -----------------------------
# WRITE MAPPING LOG
# -----------------------------
output.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "raw_name",
    "canonical_name",
    "entity_type",
    "source_url",
    "matched",
    "startup_name",
]

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )

    writer.writeheader()
    writer.writerows(rows)


total = len(rows)
matched = sum(1 for r in rows if r["matched"])
unmatched = total - matched

print("=" * 70)
print("ENTITY MAPPING LOG GENERATED")
print("=" * 70)
print("Total records:", total)
print("Matched:", matched)
print("Unmatched:", unmatched)

if total:
    print("Match rate:", round(matched / total * 100, 2), "%")

print("Output:", output)
print("=" * 70)
