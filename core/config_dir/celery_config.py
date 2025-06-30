from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
from kombu.serialization import register

from core.config_dir.config import env, redis_connective_pairs, rabbit_connective_pairs
from core.utils.anything import create_bg_files_dir
from core.utils.celery_serializer import json_loads, json_dumps

create_bg_files_dir()

register(
    'serialize_asyncpg_json',
    json_dumps,
    json_loads,
    content_type='application/x-asyncpg-json',
    content_encoding='utf-8'
)

def get_host_port_bg_url(env=env):
    uvi_host = env.uvicorn_host
    if env.deployed and env.celery_worker:
        uvi_host = env.uvicorn_host_docker
    elif env.dockerized:
        uvi_host = env.internal_host
    return uvi_host

bg_link = f'{env.transfer_protocol}://{get_host_port_bg_url()}:8000/api/bg_tasks'
broker = f"pyamqp://{rabbit_connective_pairs['user']}@{rabbit_connective_pairs['host']}//"
backend_result = f"redis://{redis_connective_pairs['host']}:{redis_connective_pairs['port']}/0"

"Методы обмена"
ex_meth = 'ex_method'
exchange_mode = Exchange(ex_meth, type='direct')

"Очереди и их Роут-ключи"
mail_queue = 'mail_queue'
mail_routing_key = 'mail_routing_key'

ext_prd_queue = 'extended_product_card_queue'
large_prd_routing_key = 'prd_routing_key'

file_queue = 'file_queue'
file_routing_key = 'file_routing_key'

celery_bg = Celery(
    'core',
    broker=broker,
    backend=backend_result,

    task_serializer='serialize_asyncpg_json',
    result_serializer='serialize_asyncpg_json',
    accept_content=['serialize_asyncpg_json'],
    enable_utc=True,

    include=[
        'core.bg_tasks.multi_bg_render_data',
        'core.bg_tasks.account_recovery',
        'core.bg_tasks.celery_processing',
        'core.bg_tasks.cloud_file_downloader',
        'core.bg_tasks.regular_crons'
    ]
)
celery_bg.conf.timezone = 'Europe/Moscow'
celery_bg.conf.enable_utc = False
celery_bg.conf.result_expires = 600

celery_bg.conf.tasks_queues = [
    Queue(ext_prd_queue, exchange=exchange_mode, routing_key=large_prd_routing_key),
    Queue(mail_queue, exchange=exchange_mode, routing_key=mail_routing_key),
    Queue(file_queue, exchange=exchange_mode, routing_key=file_routing_key)
]

celery_bg.conf.beat_schedule = {
    'expired_rT_cleaner': {
        'task': 'core.bg_tasks.celery_processing.run_rT_cleaner',
        'schedule': crontab(day_of_month={13, 28})
    },
    'trash_messages_cleaner': {
        'task': 'core.bg_tasks.celery_processing.run_messages_cleaner',
        'schedule': crontab(day_of_week=4)
    },
    's3_kharon': {
        'task': 'core.bg_tasks.celery_processing.transfer_to_s3',
        'schedule': crontab(minute=0, hour='*')
    }
}
