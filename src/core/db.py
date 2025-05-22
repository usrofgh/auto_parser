from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.settings import Settings

engine = create_async_engine(
    url=Settings().psql_dsn.get_secret_value(),
)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
