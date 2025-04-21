from fastapi import FastAPI
from routers import spimex_results

from redis import asyncio as aioredis

from cache_fastapi.cacheMiddleware import CacheMiddleware
from cache_fastapi.Backends.redis_backend import RedisBackend

REDIS_URL = aioredis.from_url("redis://localhost")


cached_endpoints = [
    '/results'
]


app = FastAPI()
backend = RedisBackend()

app.add_middleware(CacheMiddleware, cached_endpoints=cached_endpoints, backend=backend)


app.include_router(spimex_results.router)


