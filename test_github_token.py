import os
import asyncio
import aiohttp

async def main():

    token = os.getenv("GITHUB_TOKEN")

    print("Token exists:", bool(token))
    print("Token length:", len(token) if token else 0)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(
            "https://api.github.com/user",
            headers=headers
        ) as response:

            print("GitHub status:", response.status)
            print((await response.text())[:300])


if __name__ == "__main__":
    asyncio.run(main())
