import asyncio
from random import choice

from httpx import AsyncClient

from src.core.settings import Settings
from src.parsers.ria.headers import HEADERS
from src.parsers.ria.ria_parser import RiaParser
from src.third.webshare import WebShare


def initialize_client_pool(proxy_list: list[str]) -> list[AsyncClient]:
    client_pool = []
    proxies = proxy_list.copy()
    print("INITIALIZE CLIENT POOL...")
    for _ in range(len(proxy_list)):
        proxy = choice(proxies)
        proxies.remove(proxy)
        client = AsyncClient(proxy=proxy, timeout=15, headers=HEADERS)
        client_pool.append(client)
    print(f"INITIALIZED {len(client_pool)} CLIENTS")
    return client_pool


def initialize_parser() -> RiaParser:
    settings = Settings()
    webshare = WebShare(settings.WEBSHARE_API_KEY.get_secret_value())
    proxy_list = webshare.get_proxies(100)  # TODO:
    client_pool = initialize_client_pool(proxy_list)
    ria_parser = RiaParser(client_pool)
    return ria_parser


async def main():
    parser = initialize_parser()
    print("RUN PARSER")
    await parser.run()


if __name__ == "__main__":
    asyncio.run(main())
