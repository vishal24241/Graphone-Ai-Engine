import asyncio
import random
from typing import Optional

import aiohttp


GITHUB_API = "https://api.github.com"
MAX_RETRIES = 5
BASE_DELAY = 2


async def fetch_github_stars(
    github_url: str,
    session: aiohttp.ClientSession
) -> int:

    if not github_url:
        return 0

    parts = github_url.rstrip("/").split("/")

    if len(parts) < 2:
        return 0

    owner = parts[-2]
    repo = parts[-1]

    api_url = f"{GITHUB_API}/repos/{owner}/{repo}"

    for attempt in range(MAX_RETRIES):

        try:

            async with session.get(
                api_url,
                timeout=aiohttp.ClientTimeout(total=20),
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "GraphOne-AI-Engine"
                }
            ) as response:

                if response.status == 200:

                    data = await response.json()

                    return int(
                        data.get(
                            "stargazers_count",
                            0
                        )
                    )

                if response.status == 404:
                    print(
                        f"GitHub repo not found: {owner}/{repo}"
                    )
                    return 0

                if response.status == 429:

                    delay = BASE_DELAY * (2 ** attempt)

                    print(
                        f"GitHub 429. "
                        f"Retrying in {delay}s..."
                    )

                    await asyncio.sleep(delay)
                    continue

                if response.status >= 500:

                    delay = BASE_DELAY * (2 ** attempt)

                    print(
                        f"GitHub server error "
                        f"{response.status}. "
                        f"Retrying in {delay}s..."
                    )

                    await asyncio.sleep(delay)
                    continue

                print(
                    f"GitHub API returned "
                    f"status {response.status}"
                )

                return 0

        except (
            aiohttp.ClientError,
            asyncio.TimeoutError
        ) as e:

            delay = (
                BASE_DELAY * (2 ** attempt)
                + random.uniform(0, 1)
            )

            print(
                f"GitHub request error: {e}. "
                f"Retrying in {delay:.1f}s..."
            )

            await asyncio.sleep(delay)

        except Exception as e:

            print(
                f"GitHub API error: {e}"
            )

            return 0

    return 0
