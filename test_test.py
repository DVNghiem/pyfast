import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://python.org") as response:
            print("Status:", response.status)
            print("Content-type:", response.headers["content-type"])

            html = await response.json()
            print(html)


asyncio.run(main())
