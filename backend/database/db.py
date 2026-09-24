import os
import json
import tempfile
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.schema import Base

logger = get_logger("Database")

IS_TESTING = os.getenv("TESTING", "").lower() in ("true", "1", "yes")
IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("LAMBDA_TASK_ROOT"))


def _json_serializer(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def _dumps(obj):
    return json.dumps(obj, default=_json_serializer)


def _get_sqlite_url(db_name: str = "cas_dev.db") -> str:
    if IS_SERVERLESS:
        temp_dir = tempfile.gettempdir().replace("\\", "/")
        return f"sqlite+aiosqlite:///{temp_dir}/{db_name}"
    return f"sqlite+aiosqlite:///{db_name}"


def _resolve_database_url() -> tuple[str, bool]:
    """
    Resolves the active database URL and whether it is an SQLite driver.
    """
    if IS_TESTING:
        test_url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        return test_url, "sqlite" in test_url

    configured_url = os.getenv("DATABASE_URL", settings.DATABASE_URL or "").strip()

    # Normalise standard postgres url schemes if provided by cloud platforms (Supabase, Neon, etc.)
    if configured_url.startswith("postgres://"):
        configured_url = configured_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif configured_url.startswith("postgresql://") and not configured_url.startswith("postgresql+asyncpg://"):
        configured_url = configured_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # In serverless environment (Vercel/Lambda), if DATABASE_URL is default localhost or empty:
    # do NOT attempt connecting to localhost:5432 because it will timeout / fail
    if IS_SERVERLESS and (not configured_url or "localhost" in configured_url or "127.0.0.1" in configured_url):
        logger.info(f"Serverless environment detected (Vercel={IS_SERVERLESS}). Defaulting to serverless SQLite storage.")
        return _get_sqlite_url(), True

    if "sqlite" in configured_url:
        return configured_url, True

    return configured_url, False


ACTIVE_DATABASE_URL, IS_SQLITE = _resolve_database_url()


def _create_engine_instance(url: str, is_sqlite: bool):
    if is_sqlite:
        if ":memory:" in url:
            return create_async_engine(
                url,
                echo=False,
                json_serializer=_dumps,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            json_serializer=_dumps,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        url,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=10,
        pool_pre_ping=True,
        json_serializer=_dumps,
    )


engine = _create_engine_instance(ACTIVE_DATABASE_URL, IS_SQLITE)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Alias for memory/service modules expecting async_session_factory
async_session_factory = AsyncSessionLocal


async def init_db():
    """Initializes the database schema tables with multi-tier fallback."""
    global engine, AsyncSessionLocal

    # Tier 1: Try current engine
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database schema initialized successfully on {engine.url.render_as_string(hide_password=True)}")
        return
    except Exception as e:
        logger.warning(f"Primary database connection error on {engine.url.render_as_string(hide_password=True)}: {e}")

    # Tier 2: Try file-based SQLite in temp / local directory
    try:
        sqlite_url = _get_sqlite_url()
        logger.warning(f"Falling back to SQLite database ({sqlite_url})...")
        engine = _create_engine_instance(sqlite_url, is_sqlite=True)
        AsyncSessionLocal.configure(bind=engine)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite database initialized successfully.")
        return
    except Exception as sqlite_err:
        logger.warning(f"File SQLite initialization failed: {sqlite_err}. Falling back to in-memory SQLite...")

    # Tier 3: In-memory SQLite (guaranteed to succeed in any restricted environment)
    try:
        mem_url = "sqlite+aiosqlite:///:memory:"
        engine = _create_engine_instance(mem_url, is_sqlite=True)
        AsyncSessionLocal.configure(bind=engine)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("In-memory SQLite database initialized successfully.")
    except Exception as mem_err:
        logger.error(f"In-memory SQLite initialization error: {mem_err}")


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
