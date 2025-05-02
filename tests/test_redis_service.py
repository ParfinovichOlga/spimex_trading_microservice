import pytest
import datetime
from service.redis_service import get_cache_key, get_cache_ttl

FAKE1 = datetime.datetime(year=2025, month=5, day=1, hour=14, minute=11)
FAKE2 = datetime.datetime(year=2025, month=5, day=1, hour=14, minute=9)


@pytest.mark.asyncio
async def test_get_cache_key(mocker):
    req = mocker.MagicMock()
    req.method = 'GET'
    req.url.path = 'test/test_results'
    req.query_params = 'some_query'
    assert await get_cache_key(req) == 'test/test_results/GET?some_query'


@pytest.fixture
def override_now_after_14_11(monkeypatch):
    class MyDatetime:
        @classmethod
        def now(cls):
            return FAKE1

    monkeypatch.setattr(datetime, 'datetime', MyDatetime)


@pytest.fixture
def override_now_before_14_11(monkeypatch):
    class MyDatetime:
        @classmethod
        def now(cls):
            return FAKE2
    monkeypatch.setattr(datetime, 'datetime', MyDatetime)


@pytest.mark.asyncio
async def test_get_cache_ttl1(override_now_after_14_11):
    assert await get_cache_ttl() == 86400


@pytest.mark.asyncio
async def test_get_cache_ttl2(override_now_before_14_11):
    assert await get_cache_ttl() == 120

