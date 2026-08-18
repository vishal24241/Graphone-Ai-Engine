import os
import asyncio
import aiohttp

async def main():
    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.github.com/rate_limit",
            headers=headers
        ) as response:
            print("Status:", response.status)
            print("Remaining:", response.headers.get("X-RateLimit-Remaining"))
            print("Limit:", response.headers.get("X-RateLimit-Limit"))
            print("Reset:", response.headers.get("X-RateLimit-Reset"))
            print("Retry-After:", response.headers.get("Retry-After"))
            print((await response.text())[:1000])

if __name__ == "__main__":
    asyncio.run(main())
