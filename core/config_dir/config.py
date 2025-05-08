from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from asyncpg import create_pool


class Settings(BaseSettings):
    pythonpath: str
    pg_user: str
    pg_password: str
    pg_db: str
    pg_host: str
    pg_port: int
    uvicorn_host: str

    model_config = SettingsConfigDict(env_file='.env')

@lru_cache
def get_env_vars():
    return Settings()


async def set_session():
    connection = await create_pool(
        user=get_env_vars().pg_user,
        password=get_env_vars().pg_password,
        host=get_env_vars().pg_host,
        port=get_env_vars().pg_port,
        database=get_env_vars().pg_db,
        command_timeout=60
    )
    async with connection.acquire() as session:
        yield session

