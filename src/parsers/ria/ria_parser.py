import asyncio
import traceback
from asyncio import Semaphore
from random import choice, uniform

import httpx
from httpx import AsyncClient
from lxml.etree import LxmlError
from lxml.html import fromstring

from src.core.retrier import httpx_retry_on_failure
from src.parsers.ria.card_parser import CardParser
from src.parsers.ria.model import LinkType, ParseStatus, RiaCardLinkModel, RiaErrorModel
from src.parsers.ria.repository import RiaCardLinkRepository, RiaCardRepository, RiaLinkErrorRepository
from src.parsers.ria.schemas import LinkObserverSchema, RiaErrorSchema


class RiaParser:
    def __init__(self, client_pool: list[AsyncClient]):
        self._card_repository = RiaCardRepository()
        self._link_repository = RiaCardLinkRepository()
        self._error_repository = RiaLinkErrorRepository()

        self._card_parser = CardParser()
        self._base_url = "https://auto.ria.com/uk/search/?indexName=auto&country.import.usa.not=-1&price.currency=1&abroad.not=0&custom.not=1&page={}&size=100"  # noqa
        self._client_pool = client_pool
        self._semaphore = Semaphore(value=20)

    async def run(self) -> None:

        total_pages = await self._get_count_of_pages()
        total_pages = 1  # TODO:

        await asyncio.gather(*[self._parse_card_links(page_n, total_pages) for page_n in range(total_pages)])
        total_cards = await self._link_repository.count(status=ParseStatus.NEW)

        print("PARSE CARDS AND SAVE BATCHES...")
        async for batch in self._link_repository.stream(status=ParseStatus.NEW):

            cards = await asyncio.gather(*[self._parse_card(link_model, total_cards) for link_model in batch])
            cards = [card for card in cards if card]  # Delete empty {} which appeared because of errors

            await self._card_repository.create_bulk_without_conflict(cards, index_elements=["url"])

            proceed_card_links = [card["url"] for card in cards]
            await self._link_repository.update_status_by_urls(proceed_card_links, ParseStatus.PROCEED)
        await self._link_repository.bulk_delete(is_under_delete=True)
        print()

    async def retry_failed_links(self) -> None:
        print("RETRY FAILED LINKS...")
        async for batch in self._error_repository.stream(status=ParseStatus.ERROR, link_type=LinkType.PAGE_LINK):
            await asyncio.gather(*[self._parse_retry_card_links(link_model.url, len(batch)) for link_model in batch])
        await self._error_repository.bulk_delete(is_under_delete=True)

        async for batch in self._error_repository.stream(status=ParseStatus.ERROR, link_type=LinkType.CARD):
            cards = await asyncio.gather(*[self._parse_retry_card(link_model, len(batch)) for link_model in batch])
            cards = [card for card in cards if card]
            await self._card_repository.create_bulk_without_conflict(cards, index_elements=["url"])

            proceed_card_links = [card["url"] for card in cards]
            els = []
            for card in cards:
                el = {"url": card["url"], "status": ParseStatus.PROCEED}
                els.append(el)

            await self._link_repository.create_bulk(els)
        await self._error_repository.bulk_delete(is_under_delete=True)

        async for batch in self._link_repository.stream(status=ParseStatus.NEW):
            cards = await asyncio.gather(*[self._parse_card(link_model, len(batch)) for link_model in batch])
            cards = [card for card in cards if card]
            await self._card_repository.create_bulk_without_conflict(cards, index_elements=["url"])
            proceed_card_links = [card["url"] for card in cards]

        await self._link_repository.bulk_delete(is_under_delete=True)
        await self._link_repository.update_status_by_urls(proceed_card_links, ParseStatus.PROCEED)


    def _build_url(self, page: int) -> str:
        return self._base_url.format(page)

    @httpx_retry_on_failure()
    async def _get_count_of_pages(self) -> int:
        url = self._build_url(page=0)
        async with self._semaphore:
            response = await choice(self._client_pool).get(url=url)

        root = fromstring(response.content)
        return self._card_parser.parse_count_of_pages(root)

    @httpx_retry_on_failure()
    async def _get_phone_number(self, card_id: str, data_hash: str) -> str | None:
        params = {'hash': data_hash}
        endpoint = f"https://auto.ria.com/users/phones/{card_id}"
        response = await choice(self._client_pool).get(endpoint, params=params)
        response.raise_for_status()
        resp_data = response.json()
        phone = resp_data.get("formattedPhoneNumber", None)
        if not phone:
            return None
        phone = "38" + phone.replace(" ", "").replace("(", "").replace(")", "")
        return phone

    async def _parse_retry_card_links(self, url: str, total_pages: int):
        await asyncio.sleep(uniform(0, total_pages / 50))
        req_el = await self._error_repository.get_all(url=url, status=ParseStatus.ERROR, link_type=LinkType.PAGE_LINK)
        req_el = req_el[0]
        async with self._semaphore:
            try:
                response = await choice(self._client_pool).get(url=url)
            except httpx.HTTPError:
                error_schema = RiaErrorSchema(
                    url=url,
                    status=ParseStatus.ERROR,
                    link_type=LinkType.PAGE_LINK,
                    error_message=traceback.format_exc(),
                    count_retries=req_el.count_retries + 1
                )

                if error_schema.count_retries > 3:
                    error_schema.status = ParseStatus.DEAD
                await self._error_repository.update(req_el.id, link_schema.model_dump(exclude_none=True))
                return

        root = fromstring(response.content)
        links = self._card_parser.parse_card_links(root)
        print(f"INSERTING {len(links)} COMMON LINKS...")
        model_obj = {"url": None, "status": ParseStatus.NEW}
        els = []
        for link in links:
            el = model_obj.copy()
            el["url"] = link
            els.append(el)

        await self._link_repository.create_bulk_without_conflict(els, index_elements=["url"])
        await self._error_repository.update(req_el.id, {"is_under_delete": True})

    @httpx_retry_on_failure()
    async def _parse_card_links(self, page_number: int, total_pages: int) -> None:

        await asyncio.sleep(uniform(0, total_pages / 50))  # TODO:
        print(f"PARSE CARDS LINKS ON PAGE {page_number}")
        url = self._base_url.format(page_number)
        async with self._semaphore:
            try:
                response = await choice(self._client_pool).get(url=url)
                root = fromstring(response.content)
                links = self._card_parser.parse_card_links(root)
                if not links:
                    raise httpx.HTTPError("NOT LOADED A PAGE WITH LINKS")
            except httpx.HTTPError:
                print(f"[PAGE NUMBER {page_number}] ERROR")
                link_schema = RiaErrorSchema(
                    url=url,
                    status=ParseStatus.ERROR,
                    link_type=LinkType.PAGE_LINK,
                    error_message=traceback.format_exc()
                )
                await self._error_repository.create(link_schema.model_dump(exclude_none=True))
                return

        print(f"INSERTING {len(links)} COMMON LINKS...")
        model_obj = {"url": None, "status": ParseStatus.NEW}
        els = []
        for link in links:
            el = model_obj.copy()
            el["url"] = link
            els.append(el)

        await self._link_repository.create_bulk_without_conflict(els, index_elements=["url"])


    @httpx_retry_on_failure()
    async def _parse_retry_card(self, link_model: RiaErrorModel, total_cards: int) -> dict:
        await asyncio.sleep(uniform(0, total_cards / 50))  # TODO:
        print(f"PARSE {link_model.url}")
        async with self._semaphore:
            try:
                response = await choice(self._client_pool).get(url=link_model.url)
            except httpx.HTTPError:
                print(f"[CARD {link_model.url}] ERROR")
                error_schema = RiaErrorSchema(
                    url=link_model.url,
                    status=ParseStatus.ERROR,
                    link_type=LinkType.CARD,
                    error_message=traceback.format_exc(),
                    count_retries=link_model.count_retries + 1
                )
                if error_schema.count_retries > 3:
                    error_schema.status = ParseStatus.DEAD

                await self._error_repository.update(link_model.id, error_schema.model_dump(exclude_none=True))
                return {}

        root = fromstring(response.content)
        try:
            data_hash = self._card_parser.extract_data_hash(root)
            card_id = self._card_parser.extract_card_id(root)
            async with self._semaphore:
                phone_number = None
                if data_hash:
                    phone_number = await self._get_phone_number(card_id, data_hash)

                parsed_card = self._card_parser.parse_card(root, link_model.url, phone_number)
                await self._error_repository.update(link_model.id, {"is_under_delete": True})
                return parsed_card
        except (httpx.HTTPError, LxmlError, IndexError):
            print(f"[CARD {link_model.url}] ERROR")
            error_schema = RiaErrorSchema(
                url=link_model.url,
                status=ParseStatus.ERROR,
                link_type=LinkType.CARD,
                error_message=traceback.format_exc(),
                count_retries=link_model.count_retries + 1
            )
            if error_schema.count_retries > 3:
                error_schema.status = ParseStatus.DEAD

            await self._error_repository.update(link_model.id, error_schema.model_dump(exclude_none=True))
            return {}



    @httpx_retry_on_failure()
    async def _parse_card(self, link_model: RiaCardLinkModel, total_cards: int) -> dict:
        await asyncio.sleep(uniform(0, total_cards / 50))  # TODO:
        print(f"PARSE {link_model.url}")
        async with self._semaphore:
            try:
                response = await choice(self._client_pool).get(url=link_model.url)
            except httpx.HTTPError:
                print(f"[CARD {link_model.url}] ERROR")
                error_schema = RiaErrorSchema(
                    url=link_model.url,
                    status=ParseStatus.ERROR,
                    link_type=LinkType.CARD,
                    error_message=traceback.format_exc(),
                )
                await self._error_repository.create(error_schema.model_dump(exclude_none=True))
                await self._link_repository.update(link_model.id, {"is_under_delete": True})
                return {}

        root = fromstring(response.content)
        try:
            data_hash = self._card_parser.extract_data_hash(root)
            card_id = self._card_parser.extract_card_id(root)
            async with self._semaphore:
                phone_number = None
                if data_hash:
                    phone_number = await self._get_phone_number(card_id, data_hash)
                return self._card_parser.parse_card(root, link_model.url, phone_number)
        except (httpx.HTTPError, LxmlError, IndexError):
            print(f"[CARD {link_model.url}] ERROR")
            error_schema = RiaErrorSchema(
                url=link_model.url,
                status=ParseStatus.ERROR,
                link_type=LinkType.CARD,
                error_message=traceback.format_exc(),
            )
            await self._error_repository.create(error_schema.model_dump(exclude_none=True))
            await self._link_repository.update(link_model.id, {"is_under_delete": True})
            return {}
