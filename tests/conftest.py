import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from models.spimex import SpimexTradingResults
from backend.db import Base
from typing import AsyncGenerator
from datetime import date, timedelta
from main import app
from backend.db_depends import get_db
from config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession


@pytest.fixture(autouse=True)
def check_mode():
    assert settings.MODE == "TEST"


@pytest_asyncio.fixture(scope='function', autouse=True)
async def disable_get_cache(mocker):
    """Patch get cache."""
    mocker.patch('service.redis_service.get_cache', return_value=None)


@pytest_asyncio.fixture(scope='function', autouse=True)
async def disable_set_cache(mocker):
    """Patch set cache."""
    mocker.patch('service.redis_service.set_cache', return_value=None)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def engine():
    """Create test SQLAlchemy engine."""
    test_eng = create_async_engine(settings.DATABASE_URL)
    async with test_eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield test_eng
    finally:
        async with test_eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test db session."""
    session_local = async_sessionmaker(expire_on_commit=False, class_=AsyncSession, bind=engine)
    async with session_local() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db):
    """Create http client for test."""
    async def override_get_db():
        """Override session: get test session."""
        yield db

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test')as client:
        app.dependency_overrides[get_db] = override_get_db
        yield client


def create_data_for_trade(**params):
    """Sample of trade"""
    defaults = {
        'exchange_product_id': 'A100STI060F',
        'exchange_product_name': 'Some test name',
        'oil_id': 'A100',
        'delivery_basis_id': 'STI',
        'delivery_basis_name': 'st',
        'delivery_type_id': 'F',
        'volume': 10,
        'total': 10,
        'count': 10,
        'date': date.today(),
        'created_on': date.today(),
        'updated_on': date.today()
    }
    defaults.update(params)
    return defaults


@pytest_asyncio.fixture(scope='function')
async def create_list_trade(db):
    """Insert data into test db."""
    trades = [
        create_data_for_trade(),
        create_data_for_trade(
            exchange_product_id='DSC5LSA100U', oil_id='DSC5',
            delivery_basis_id='LSA', delivery_type_id='U', date=date.today() - timedelta(days=1)),
        create_data_for_trade(date=date.today() - timedelta(days=2))
    ]

    for t in trades:
        trade = SpimexTradingResults(**t)
        db.add(trade)
        await db.commit()
        await db.refresh(trade)

    yield trades
