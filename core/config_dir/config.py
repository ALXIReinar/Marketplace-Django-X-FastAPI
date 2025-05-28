import os
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
    pg_host_docker: str
    pg_port: int
    pg_port_docker: int

    redis_host: str
    redis_port: str

    elastic_user: str
    elastic_password: str
    elastic_host: str
    elastic_port: str
    elastic_certs: str
    elastic_certs_docker: str
    search_index: str

    s3_access_key: str
    s3_secret_key: str
    s3_endpoint_url: str
    s3_bucket_name: str

    rabbitmq_user: str

    celery_broker_url: str
    celery_result_backend: str

    JWTs: AuthConfig = AuthConfig()
    uvicorn_host: str
    dockerized: str | bool = os.getenv('DOCKERIZED', False)

    model_config = SettingsConfigDict(env_file='.env', extra='allow')

@lru_cache
def get_env_vars():
    return Settings()
env = get_env_vars()

"ElasticSearch"
es_client = AsyncElasticsearch(
    hosts=[
        f'https://{env.elastic_host}:{env.elastic_port}'
    ],
    basic_auth=(env.elastic_user,env.elastic_password),
    ca_certs=env.elastic_certs_docker if env.dockerized else env.elastic_certs,
    verify_certs=False
)


"PostgreSql"
pool_settings = dict(
    user=env.pg_user,
    password=env.pg_password,
    host=env.pg_host_docker if env.dockerized else env.pg_host,
    port=env.pg_port_docker if env.dockerized else env.pg_port,
    database=env.pg_db,
    command_timeout=60
)

async def set_session():
    connection = await create_pool(**pool_settings)
    async with connection.acquire() as session:
        yield session


"S3 Storage"
@asynccontextmanager
async def cloud_session():
        config =  {
            'aws_access_key_id': env.access_key,
            'aws_secret_access_key': env.secret_key,
            'endpoint_url': env.endpoint_url,
        }
        async with get_session().create_client('s3', **config) as session:
            yield session
