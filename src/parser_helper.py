import asyncio

from src.main import initialize_parser


async def helper_parser():
    print("RUN PARSER HELPER")
    parser = initialize_parser()
    await parser.retry_failed_links()


if __name__ == "__main__":
    asyncio.run(helper_parser())
