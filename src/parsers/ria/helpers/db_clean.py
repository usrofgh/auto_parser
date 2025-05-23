import asyncio

from src.core.db import session_maker
from sqlalchemy import text


async def db_clean():
    async with session_maker() as db:
        await db.execute(text("DELETE FROM ria_card_links"))
        await db.execute(text("DELETE FROM ria_cards"))
        await db.execute(text("DELETE FROM ria_errors"))
        await db.commit()


if __name__ == '__main__':
    asyncio.run(db_clean())
