import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Configure testing environment variables
os.environ["TESTING"] = "true"
os.environ["TEST_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from backend.database.schema import Base
from backend.database.db import engine, AsyncSessionLocal


@pytest.fixture(scope="session")
def test_contract_text() -> str:
    path = os.path.join(os.path.dirname(__file__), "../../contracts/enterprise_saas_vendor_contract.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
