import asyncio

from src.core.logger import logger
from src.main import initialize_parser


async def helper_parser():
    logger.info("RUN PARSER HELPER")
    parser = initialize_parser()
    await parser.retry_failed_links()


if __name__ == "__main__":
    asyncio.run(helper_parser())
