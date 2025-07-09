from contextlib import asynccontextmanager
from typing import Annotated

from fastapi.params import Depends
from redis.asyncio.client import Redis
from core.config_dir.config import redis_connective_pairs


@asynccontextmanager
async def get_redis_connection():
    redis = Redis(**redis_connective_pairs)
    try:
        yield redis
    finally:
        await redis.close()

async def redis_pool():
    redis = Redis(**redis_connective_pairs)
    try:
        yield redis
    finally:
        await redis.close()

RedisDep = Annotated[Redis, Depends(redis_pool)]