from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from asyncpg import create_pool


WORKDIR = Path(__file__).resolve().parent.parent.parent

app = FastAPI()
encryption = CryptContext(schemes=['bcrypt'], deprecated='auto')


class AuthConfig(BaseModel):
    private_key: Path = WORKDIR / 'keys' / 'private_jwt.pem'
    public_key: Path = WORKDIR / 'keys' / 'public_jwt.pem'
    algorithm: str = 'RS256'
    ttl_aT: timedelta = timedelta(minutes=15)
    ttl_rT: timedelta = timedelta(days=30)


class Settings(BaseSettings):
    abs_path: str = str(WORKDIR)

    pg_user: str
    pg_password: str
    pg_db: str
    pg_host: str
    pg_port: int

    JWTs: AuthConfig = AuthConfig()
    uvicorn_host: str
    redis_host: str

    model_config = SettingsConfigDict(env_file='.env')

@lru_cache
def get_env_vars():
    return Settings()


pool_settings = dict(
    user=get_env_vars().pg_user,
    password=get_env_vars().pg_password,
    host=get_env_vars().pg_host,
    port=get_env_vars().pg_port,
    database=get_env_vars().pg_db,
    command_timeout=60
)


async def set_session():
    connection = await create_pool(**pool_settings)
    async with connection.acquire() as session:
        yield session

