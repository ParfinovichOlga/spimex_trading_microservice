import redis
from datetime import datetime
from config import REDIS_PORT, REDIS_HOST, CACHE_STORAGE_TIME
from fastapi import Request

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


async def get_cache_ttl() -> int:
    """Get cache ttl in seconds before 14:11."""
    now = datetime.now()
    now_in_seconds = now.hour * 60 * 60 + now.minute * 60
    storage_time = int(CACHE_STORAGE_TIME)
    if now_in_seconds < storage_time:
        return storage_time - now_in_seconds
    else:
        return 24 * 60 * 60 - now_in_seconds + storage_time


async def get_cache_key(request: Request) -> str:
    """Generate key for storaging cache."""
    return f'{request.url.path}/{request.method}?{request.query_params}'


async def get_cache(request: Request):
    """Get cashed data."""
    key = await get_cache_key(request)
    return redis_client.get(key)


async def set_cache(request: Request, data: str):
    """Storage data to cache."""
    k = await get_cache_key(request)
    cache_ttl = await get_cache_ttl()
    redis_client.set(k, data, ex=cache_ttl)
