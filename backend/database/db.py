import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.schema import Base

logger = get_logger("Database")

# Determine connection URL
# Production uses PostgreSQL via asyncpg
DATABASE_URL = settings.DATABASE_URL
IS_TESTING = os.getenv("TESTING", "").lower() in ("true", "1", "yes")

import json

def _json_serializer(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)

def _dumps(obj):
    return json.dumps(obj, default=_json_serializer)

from sqlalchemy.pool import StaticPool

# For automated test suites when external Postgres is not running, test runner can toggle sqlite in-memory
if IS_TESTING and "sqlite" in os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:"):
    TEST_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    engine = create_async_engine(
        TEST_URL,
        echo=False,
        json_serializer=_dumps,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=10,
        pool_pre_ping=True,
        json_serializer=_dumps,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Alias for memory/service modules expecting async_session_factory
async_session_factory = AsyncSessionLocal


async def init_db():
    """Initializes the database schema tables."""
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database schema initialized successfully on {engine.url.render_as_string(hide_password=True)}")
    except Exception as e:
        logger.warning(f"Database connection error on {engine.url.render_as_string(hide_password=True)}: {e}")
        if not IS_TESTING and "postgresql" in str(engine.url):
            logger.warning("PostgreSQL is unreachable. Falling back to local SQLite database (cas_dev.db)...")
            fallback_url = "sqlite+aiosqlite:///cas_dev.db"
            engine = create_async_engine(
                fallback_url,
                echo=settings.DEBUG,
                json_serializer=_dumps,
            )
            AsyncSessionLocal.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Local SQLite database (cas_dev.db) initialized successfully.")
        elif not IS_TESTING:
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions to FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
