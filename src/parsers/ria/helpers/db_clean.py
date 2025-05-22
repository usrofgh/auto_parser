import asyncio

from src.core.db import session_maker


async def db_clean():
    async with session_maker() as db:
        from sqlalchemy import text
        await db.execute(text("DELETE FROM ria_links"))
        await db.execute(text("DELETE FROM ria"))
        await db.commit()


if __name__ == '__main__':
    asyncio.run(db_clean())
