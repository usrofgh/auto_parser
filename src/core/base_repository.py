from abc import ABC
from typing import AsyncIterable, Generic, TypeVar

from pydantic import UUID4
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from src.core.base_model import BaseModel
from src.core.db import session_maker

ModelG = TypeVar("ModelG", bound=BaseModel)


class BaseRepository(ABC, Generic[ModelG]):
    MODEL: type[ModelG] = None

    def __init__(self):
        if not self.MODEL:
            raise NotImplementedError("SPECIFY MODEL")

    async def create(self, obj_data: dict) -> None:
            stmt = insert(self.MODEL).values(**obj_data)
            async with session_maker() as db:
                await db.execute(stmt)
                await db.commit()


    async def create_without_conflict(self, obj_data: dict, index_elements: list) -> None:
        stmt = insert(self.MODEL).values(**obj_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
        async with session_maker() as db:
            await db.execute(stmt)
            await db.commit()


    async def create_bulk(self, object_datas: list[dict]) -> None:
        stmt = insert(self.MODEL)
        async with session_maker() as db:
            await db.execute(stmt, object_datas)
            await db.commit()


    async def create_bulk_without_conflict(self, object_datas: list[dict], index_elements: list) -> None:
        stmt = insert(self.MODEL).on_conflict_do_nothing(index_elements=index_elements)
        async with session_maker() as db:
            await db.execute(stmt, object_datas)
            await db.commit()

    async def get_by_id(self, id_: UUID4) -> ModelG:
        stmt = select(self.MODEL).where(self.MODEL.id == id_)
        async with session_maker() as db:
            result = await db.execute(stmt)
        return result.scalars().one_or_none()

    async def get_all(self, **filters) -> list[ModelG]:
        offset = filters.pop("offset", 0)
        limit = filters.pop("limit", 100)
        stmt = select(self.MODEL).filter_by(**filters).offset(offset).limit(limit)
        async with session_maker() as db:
            result = await db.execute(stmt)
        return list(result.scalars().all())


    async def update(self, id_: UUID4, update_data: dict) -> ModelG:
        stmt = update(self.MODEL).where(self.MODEL.id == id_).values(**update_data).returning(self.MODEL)
        async with session_maker() as db:
            result = await db.execute(stmt)
            await db.commit()

        updated_record = result.scalars().first()
        return updated_record


    async def delete(self, id_: UUID4) -> None:
        stmt = delete(self.MODEL).where(self.MODEL.id == id_)
        async with session_maker() as db:
            await db.execute(stmt)
            await db.commit()


    async def count(self, **filters) -> int:
        stmt = select(func.count("*")).select_from(self.MODEL).filter_by(**filters)
        async with session_maker() as db:
            result = await db.execute(stmt)
        return result.scalar_one()

    async def stream(self, batch_size: int = 1000, **filters) -> AsyncIterable[list[ModelG]]:
        offset = 0
        while True:
            batch = await self.get_all(**filters, offset=offset, limit=batch_size)
            if not batch:
                break
            yield batch
            offset += len(batch)
