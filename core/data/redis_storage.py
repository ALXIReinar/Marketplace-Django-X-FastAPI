from contextlib import asynccontextmanager
from typing import Annotated

from fastapi.params import Depends
from redis.asyncio.client import Redis
from core.config_dir.config import env


@asynccontextmanager
async def get_redis_connection():
    redis = Redis(host=env.redis_host if not env.dockerized else env.redis_host_docker,
                      port=env.redis_port if not env.dockerized else env.redis_port_docker)
    try:
        yield redis
    finally:
        await redis.close()

async def redis_pool():
    redis = Redis(host=env.redis_host if not env.dockerized else env.redis_host_docker,
                  port=env.redis_port if not env.dockerized else env.redis_port_docker)
    try:
        yield redis
    finally:
        await redis.close()

RedisDep = Annotated[Redis, Depends(redis_pool)]