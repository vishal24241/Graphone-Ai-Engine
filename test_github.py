import os
import asyncio
import aiohttp

TOKEN = os.getenv("GITHUB_TOKEN")

async def main():
    url = "https://api.github.com/search/repositories"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GraphOne-AI-Research-Pipeline"
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    params = {
        "q": "AutoDesign AI",
        "per_page": 5
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
            params=params
        ) as response:

            print("Status:", response.status)

            data = await response.json()

            print("Total results:", data.get("total_count"))

            for repo in data.get("items", []):
                print(repo.get("full_name"))
                print(repo.get("html_url"))
                print()

asyncio.run(main())