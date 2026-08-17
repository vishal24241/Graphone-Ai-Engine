import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TARGET = 1000
BATCH_SIZE = 100
DELAY_SECONDS = 3

OUTPUT = "research_papers.json"
TEMP = "research_papers.json.tmp"

ARXIV_API = "https://export.arxiv.org/api/query"

NS = {
    "atom": "http://www.w3.org/2005/Atom"
}


def load_existing():
    if not os.path.exists(OUTPUT):
        return []

    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, list) else []

    except Exception:
        return []


def fetch_batch(start, size):
    params = {
        "search_query": "cat:cs.AI",
        "start": start,
        "max_results": size,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    url = ARXIV_API + "?" + urllib.parse.urlencode(params)

    for attempt in range(4):
        try:
            print(f"Fetching batch: start={start}, size={size}")

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "GraphOne-AI-Engineer-Demo/1.0"
                }
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)

            papers = []

            for entry in root.findall("atom:entry", NS):

                title = entry.findtext(
                    "atom:title",
                    "",
                    NS
                ).strip().replace("\n", " ")

                summary = entry.findtext(
                    "atom:summary",
                    "",
                    NS
                ).strip()

                published = entry.findtext(
                    "atom:published",
                    "",
                    NS
                ).strip()

                arxiv_url = entry.findtext(
                    "atom:id",
                    "",
                    NS
                ).strip()

                authors = []

                for author in entry.findall(
                    "atom:author",
                    NS
                ):
                    name = author.findtext(
                        "atom:name",
                        "",
                        NS
                    ).strip()

                    if name:
                        authors.append(name)

                arxiv_id = arxiv_url.rstrip("/").split("/")[-1]

                # Remove version from ID
                base_arxiv_id = arxiv_id.split("v")[0]

                github_url = None

                for link in entry.findall(
                    "atom:link",
                    NS
                ):
                    href = link.attrib.get("href", "")
                    title_attr = link.attrib.get("title", "")

                    if (
                        "github" in href.lower()
                        or "github" in title_attr.lower()
                    ):
                        github_url = href
                        break

                paper = {
                    "title": title,
                    "authors": authors,
                    "arxiv_id": base_arxiv_id,
                    "paper_url": f"https://arxiv.org/abs/{base_arxiv_id}",
                    "published_date": published,
                    "huggingface_url": (
                        f"https://huggingface.co/papers/{base_arxiv_id}"
                    ),
                    "github_url": github_url
                }

                if title and base_arxiv_id:
                    papers.append(paper)

            return papers

        except Exception as e:

            print(
                f"Batch failed (attempt {attempt + 1}/4): {e}"
            )

            if attempt < 3:
                wait = 2 ** attempt + 1
                print(f"Retrying in {wait} seconds...")
                time.sleep(wait)

    return []


def save_atomic(data):

    with open(
        TEMP,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(TEMP, OUTPUT)


def main():

    existing = load_existing()

    papers_by_id = {}

    for paper in existing:

        arxiv_id = paper.get("arxiv_id")

        if arxiv_id:
            papers_by_id[arxiv_id.split("v")[0]] = paper

    print(
        f"Existing unique papers: {len(papers_by_id)}"
    )

    start = 0

    while len(papers_by_id) < TARGET:

        batch = fetch_batch(
            start,
            BATCH_SIZE
        )

        if not batch:
            print("No papers returned. Stopping.")
            break

        before = len(papers_by_id)

        for paper in batch:

            arxiv_id = paper["arxiv_id"]

            if arxiv_id not in papers_by_id:
                papers_by_id[arxiv_id] = paper

        added = len(papers_by_id) - before

        print(
            f"Batch returned: {len(batch)} | "
            f"New unique: {added} | "
            f"Total: {len(papers_by_id)}"
        )

        save_atomic(
            list(papers_by_id.values())
        )

        start += BATCH_SIZE

        if len(batch) < BATCH_SIZE:
            print("Reached end of available results.")
            break

        if len(papers_by_id) < TARGET:
            time.sleep(DELAY_SECONDS)

    final_data = list(
        papers_by_id.values()
    )[:TARGET]

    save_atomic(final_data)

    print()
    print("=" * 70)
    print("ARXIV BULK INGESTION COMPLETE")
    print("=" * 70)
    print("Target:", TARGET)
    print("Final unique papers:", len(final_data))
    print("Output:", OUTPUT)
    print("=" * 70)


if __name__ == "__main__":
    main()
