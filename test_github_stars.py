import asyncio
import aiohttp

from src.enrichment.github_metrics import fetch_github_stars


async def main():

    urls = [
        "https://github.com/Yaxin9Luo/AutoDesign",
        "https://github.com/sunblaze-ucb/vero",
        "https://github.com/AlayaLab/AlayaWorld"
    ]

    async with aiohttp.ClientSession() as session:

        for url in urls:

            stars = await fetch_github_stars(url, session)

            print(
                f"{url} -> {stars} stars"
            )


asyncio.run(main())
