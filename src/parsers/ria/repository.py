from sqlalchemy import update

from src.core.base_repository import BaseRepository
from src.core.db import session_maker
from src.parsers.ria.model import RiaCardLinkModel, RiaCardModel, RiaErrorModel


class RiaCardRepository(BaseRepository[RiaCardModel]):
    MODEL = RiaCardModel


class RiaLinkErrorRepository(BaseRepository[RiaErrorModel]):
    MODEL = RiaErrorModel


class RiaCardLinkRepository(BaseRepository[RiaCardLinkModel]):
    MODEL = RiaCardLinkModel

    async def update_status_by_urls(self, urls: list[str], new_status: str) -> None:
        stmt = (
            update(self.MODEL)
            .where(self.MODEL.url.in_(urls))
            .values(status=new_status)
        )
        async with session_maker() as db:
            await db.execute(stmt)
            await db.commit()
