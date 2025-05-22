from contextlib import asynccontextmanager
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

from aiobotocore.session import get_session
from elasticsearch import AsyncElasticsearch
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

    redis_host: str

    elastic_user: str
    elastic_password: str
    elastic_host: str
    elastic_port: str
    elastic_certs: str
    search_index: str

    s3_access_key: str
    s3_secret_key: str
    s3_endpoint_url: str
    s3_bucket_name: str

    JWTs: AuthConfig = AuthConfig()
    uvicorn_host: str

    model_config = SettingsConfigDict(env_file='.env')

@lru_cache
def get_env_vars():
    return Settings()


es_client = AsyncElasticsearch(
    hosts=[
        f'https://{get_env_vars().elastic_host}:{get_env_vars().elastic_port}'
    ],
    basic_auth=(get_env_vars().elastic_user,get_env_vars().elastic_password),
    ca_certs=get_env_vars().elastic_certs,
    verify_certs=False
)


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


@asynccontextmanager
async def cloud_session():
        config =  {
            'aws_access_key_id': get_env_vars().access_key,
            'aws_secret_access_key': get_env_vars().secret_key,
            'endpoint_url': get_env_vars().endpoint_url,
        }
        async with get_session().create_client('s3', **config) as session:
            yield session
