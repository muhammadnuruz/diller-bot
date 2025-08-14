from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import URL
from db.config import Config

Base = declarative_base()

DATABASE_URL = URL.create(
    drivername=Config.DRIVER,
    username=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME
)


class AsyncDatabaseSession:
    def __init__(self):
        self._engine = create_async_engine(DATABASE_URL, echo=False)
        self._sessionmaker = async_sessionmaker(bind=self._engine, expire_on_commit=False)

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        return self._sessionmaker()

    async def dispose(self):
        await self._engine.dispose()


db = AsyncDatabaseSession()
