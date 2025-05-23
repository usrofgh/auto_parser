import asyncio
from random import choice

from httpx import AsyncClient

from src.core.logger import logger
from src.core.settings import Settings
from src.parsers.ria.headers import HEADERS
from src.parsers.ria.helpers.db_clean import db_clean
from src.parsers.ria.ria_parser import RiaParser
from src.third.webshare import WebShare


def initialize_client_pool(proxy_list: list[str]) -> list[AsyncClient]:
    client_pool = []
    proxies = proxy_list.copy()
    logger.info("INITIALIZE CLIENT POOL...")
    for _ in range(len(proxy_list)):
        proxy = choice(proxies)
        proxies.remove(proxy)
        client = AsyncClient(proxy=proxy, timeout=15, headers=HEADERS)
        client_pool.append(client)
    logger.info(f"INITIALIZED {len(client_pool)} CLIENTS")
    return client_pool


def initialize_parser() -> RiaParser:
    settings = Settings()
    webshare = WebShare(settings.WEBSHARE_API_KEY.get_secret_value())
    proxy_list = webshare.get_proxies(100)  # TODO:
    client_pool = initialize_client_pool(proxy_list)
    ria_parser = RiaParser(client_pool)
    return ria_parser


async def main_parser():
    await db_clean()  # Clean old records. Old records are dumping in 'dumps' folder by cron
    parser = initialize_parser()
    logger.info("RUN PARSER")
    await parser.run()


if __name__ == "__main__":
    asyncio.run(main_parser())
