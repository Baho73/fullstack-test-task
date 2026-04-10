# FILE: backend/src/database.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Единая точка создания async engine и session factory. FastAPI dependency для DI сессий.
#   SCOPE: Engine creation, session factory, get_session async generator for FastAPI Depends()
#   DEPENDS: none
#   LINKS: M-DB, V-M-DB
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   engine - async SQLAlchemy engine singleton
#   async_session_maker - async session factory
#   get_session - FastAPI Depends() async generator yielding AsyncSession
# END_MODULE_MAP

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# START_BLOCK_ENGINE_SETUP
DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ.get('POSTGRES_USER', 'postgres')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
    f"{os.environ.get('PGPORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'test')}"
)

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
# END_BLOCK_ENGINE_SETUP


# START_CONTRACT: get_session
#   PURPOSE: Async generator that yields an AsyncSession for FastAPI dependency injection.
#   INPUTS: none
#   OUTPUTS: { AsyncSession - active database session }
#   SIDE_EFFECTS: Opens and closes a database session.
#   LINKS: M-APP (used via Depends())
# END_CONTRACT: get_session

# START_BLOCK_GET_SESSION
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
# END_BLOCK_GET_SESSION

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.0.0 - Extracted from service.py; single source of truth for DB connection]
# END_CHANGE_SUMMARY
