import os
import ssl
from datetime import timedelta
from functools import lru_cache
from contextlib import asynccontextmanager
from pathlib import Path

from asyncpg import create_pool
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from aiobotocore.session import get_session
from aiosmtplib import SMTP
from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel



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

    pg_db: str
    pg_user: str

    pg_password: str
    pg_host: str
    pg_port: int

    pg_password_cl: str
    pg_host_cl: str
    pg_port_cl: int

    pg_host_celery_worker_docker_db: str
    pg_host_docker: str
    pg_port_docker: int

    redis_host: str
    redis_port: str
    redis_host_docker: str
    redis_port_docker: str

    elastic_user: str
    elastic_password: str
    elastic_host: str
    elastic_host_docker: str
    elastic_port: str
    elastic_cert: str
    search_index: str

    s3_access_key: str
    s3_secret_key: str
    s3_endpoint_url: str
    s3_bucket_name: str

    rabbitmq_user: str

    celery_broker_url: str
    celery_result_backend: str

    smtp_host: str
    smtp_port: int
    smtp_host_docker: str
    smtp_port_docker: int
    smtp_tls_on: bool
    smtp_cert: str
    smtp_cert_docker: str

    JWTs: AuthConfig = AuthConfig()
    internal_host: str
    uvicorn_host: str

    mail_sender: str
    dockerized: bool = os.getenv('DOCKERIZED', False)
    docker_db: bool = os.getenv('DOCKER_DB', False)
    cloud_db: bool = os.getenv('CLOUD_DB', False)
    docker_es: bool = os.getenv('DOCKER_ES', False)
    celery_worker: bool = os.getenv('CELERY_WORKER', False)

    model_config = SettingsConfigDict(env_file='.env', extra='allow')

@lru_cache
def get_env_vars():
    return Settings()
env = get_env_vars()

"ElasticSearch"
es_host = env.elastic_host
es_settings = dict(
    basic_auth=(env.elastic_user, env.elastic_password),
    ca_certs=env.elastic_cert,
    verify_certs=False
)
if env.dockerized:
    es_host = env.elastic_host_docker
es_link = f'https://{es_host}:{env.elastic_port}'
es_settings['hosts'] = [es_link]
if env.docker_es:
    es_link = f'http://{es_host}:{env.elastic_port}'
    es_settings = dict(
        hosts=[es_link]
    )
es_client = AsyncElasticsearch(**es_settings)


"PostgreSql"
db_host = env.pg_host
db_port = env.pg_port
passw = env.pg_password
if env.cloud_db:
    "БД-Облако"
    db_host = env.pg_host_cl
    db_port = env.pg_port_cl
    passw = env.pg_password_cl
elif env.docker_db and env.celery_worker:
    "БД в Докере и запускается Воркер"
    db_host = env.pg_host_celery_worker_docker_db
elif not env.cloud_db and env.celery_worker:
    "Локальная БД и Воркер"
    db_host = env.internal_host
elif env.docker_db:
    "БД в докере, Локалка подрубается"
    db_port = env.pg_port_docker

pool_settings = dict(
    user=env.pg_user,
    password=passw,
    host=db_host,
    port=db_port,
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


"SMTP Service"
sender = "Pied Market"
smtp_context = ssl.create_default_context(cafile=env.smtp_cert if not env.dockerized else env.smtp_cert_docker)
smtp_context.check_hostname = False
smtp_context.verify_mode = ssl.CERT_NONE
smtp = SMTP(
    hostname=env.smtp_host if not env.dockerized else env.smtp_host_docker,
    port=env.smtp_port if not env.dockerized else env.smtp_port_docker,
    timeout=60,
    start_tls=env.smtp_tls_on,
    tls_context=smtp_context
)
