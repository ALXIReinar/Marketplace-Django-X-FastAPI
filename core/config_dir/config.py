import os
import ssl
from datetime import timedelta
from functools import lru_cache
from contextlib import asynccontextmanager
from pathlib import Path

from botocore.config import Config
from elasticsearch import AsyncElasticsearch
from aiobotocore.session import get_session as async_get_session
from aiosmtplib import SMTP
from broadcaster import Broadcast
from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel



WORKDIR = Path(__file__).resolve().parent.parent.parent

encryption = CryptContext(schemes=['bcrypt'], deprecated='auto')


class AuthConfig(BaseModel):
    private_key: Path = WORKDIR / 'keys' / 'private_jwt.pem'
    public_key: Path = WORKDIR / 'keys' / 'public_jwt.pem'
    algorithm: str = 'RS256'
    ttl_aT: timedelta = timedelta(minutes=15)
    ttl_rT: timedelta = timedelta(days=30)
    ttl_wT: timedelta = timedelta(seconds=60)  # timedelta(seconds=15)


class Settings(BaseSettings):
    abs_path: str = str(WORKDIR)
    local_storage: str = '/core/templates/images'
    cloud_storage: str = 'images'
    bg_users_files: str = 'user_files_bg_dumps'
    bg_upload_file_size: int = 31_457_280 # 30MB
    delta_layout_msg: int = 20

    pg_db: str
    pg_api_db: str
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
    elastic_cert_docker: str
    search_index: str

    s3_access_key: str
    s3_secret_key: str
    s3_region: str
    s3_endpoint_url: str
    s3_bucket_name: str
    s3_root_cert: str
    s3_root_cert_docker: str

    rabbitmq_user: str
    rabbitmq_passw: str
    rabbitmq_host: str
    rabbitmq_host_docker: str
    rabbitmq_port_docker: str

    smtp_host: str
    smtp_port: int
    smtp_host_docker: str
    smtp_port_docker: int
    smtp_tls_on: bool
    smtp_cert: str
    smtp_cert_docker: str

    JWTs: AuthConfig = AuthConfig()
    transfer_protocol: str
    internal_host: str
    uvicorn_host: str
    uvicorn_host_docker: str
    uvicorn_port: int
    uvicorn_port_test: int

    requests_limit: int
    ttl_requests_limit: int
    mail_sender: str
    dockerized: bool = os.getenv('DOCKERIZED', False)
    deployed: bool = os.getenv('DEPLOYED', False)
    docker_db: bool = os.getenv('DOCKER_DB', False)
    cloud_db: bool = os.getenv('CLOUD_DB', False)
    docker_es: bool = os.getenv('DOCKER_ES', False)
    celery_worker: bool = os.getenv('CELERY_WORKER', False)
    test_celery_worker: bool = os.getenv('TEST_CELERY_WORKER', False)

    model_config = SettingsConfigDict(env_file='.env', extra='allow')

@lru_cache
def get_env_vars():
    return Settings()
env = get_env_vars()

"Uvicorn"
def get_uvicorn_host(env=env):
    uvi_host = env.uvicorn_host
    if env.deployed and env.celery_worker:
        uvi_host = env.uvicorn_host_docker
    elif env.dockerized:
        uvi_host = env.internal_host
    return uvi_host

def get_uvicorn_port(env=env):
    uvi_port = env.uvicorn_port
    if env.test_celery_worker:
        uvi_port = env.uvicorn_port_test
    return uvi_port


"ElasticSearch"
def get_host_port_ES(env=env):
    es_host = env.elastic_host
    settings = dict(
        basic_auth=(env.elastic_user, env.elastic_password),
        ca_certs=env.elastic_cert if not env.dockerized else env.elastic_cert_docker,
        verify_certs=False
    )
    if env.dockerized:
        es_host = env.elastic_host_docker if env.docker_es else env.internal_host
    es_link = f'https://{es_host}:{env.elastic_port}'
    settings['hosts'] = [es_link]
    if env.docker_es:
        es_link = f'http://{es_host}:{env.elastic_port}'
        settings = dict(
            hosts=[es_link]
        )
    return settings
es_settings = get_host_port_ES()

async def get_elastic_client():
    es_client = AsyncElasticsearch(**es_settings)
    try:
        yield es_client
    finally:
        await es_client.close()


"PostgreSql"
def get_host_port_password_DB(env=env):
    db_host = env.pg_host
    db_port = env.pg_port
    passw = env.pg_password
    if env.cloud_db:
        "БД-Облако"
        db_host = env.pg_host_cl
        db_port = env.pg_port_cl
        passw = env.pg_password_cl
    elif env.deployed:
        "Фулл докер-деплой"
        db_host = env.pg_host_docker
    elif env.docker_db and env.celery_worker:
        "БД в Докере и запускается Воркер"
        db_host = env.pg_host_celery_worker_docker_db
    elif not env.cloud_db and env.celery_worker:
        "Локальная БД и Воркер"
        db_host = env.internal_host
    elif env.docker_db and not env.dockerized:
        "БД в докере, Локалка подрубается"
        db_port = env.pg_port_docker
    return dict(
        password=passw,
        host=db_host,
        port=db_port,
    )
pool_settings = dict(
    user=env.pg_user,
    **get_host_port_password_DB(),
    database=env.pg_db,
    command_timeout=60
)


"S3 Storage"
url_config = Config(
    region_name='ru-7',
    s3={'addressing_style': 'virtual'}
)
s3_config =  {
    'aws_access_key_id': env.s3_access_key,
    'aws_secret_access_key': env.s3_secret_key,
    'region_name': env.s3_region,
    'endpoint_url': env.s3_endpoint_url,
    'config': url_config,
    'verify': env.s3_root_cert_docker if env.dockerized else env.s3_root_cert
}
@asynccontextmanager
async def async_cloud_session():
    async with async_get_session().create_client('s3', **s3_config) as session:
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


"RabbitMQ"
def get_host_port_Rmq(env=env):
    host = env.rabbitmq_host_docker if env.dockerized else env.rabbitmq_host
    port = env.rabbitmq_port_docker
    user, passw = env.rabbitmq_user, env.rabbitmq_passw
    return dict(
        host=host,
        port=port,
        user=user,
        passw=passw
    )
rabbit_connective_pairs = get_host_port_Rmq()


"Redis"
def get_host_port_REDIS(env=env):
    host = env.redis_host_docker if env.dockerized else env.redis_host
    port = env.redis_port_docker if env.dockerized else env.redis_port
    return dict(
        host=host,
        port=port
    )
redis_connective_pairs = get_host_port_REDIS()


"Broadcast WebSocket"
broadcast = Broadcast(f"redis://{redis_connective_pairs['host']}:{redis_connective_pairs['port']}")
