from celery import Celery
from kombu import Exchange, Queue
from kombu.serialization import register

from core.config_dir.config import env
from core.utils.celery_serializer import json_loads, json_dumps

register(
    'serialize_asyncpg_json',
    json_dumps,
    json_loads,
    content_type='application/x-asyncpg-json',
    content_encoding='utf-8'
)


broker = env.celery_broker_url if env.dockerized else f"pyamqp://{env.rabbitmq_user}@localhost//"
backend_result = env.celery_result_backend if env.dockerized else f"redis://localhost:{env.redis_port}/0"

ex_meth = 'ex_method'
exchange_mode = Exchange(ex_meth, type='direct')

mail_queue = 'mail_queue'
mail_routing_key = 'mail_routing_key'

ext_prd_queue = 'extended_product_card_queue'
large_prd_routing_key = 'prd_routing_key'


celery_bg = Celery(
    'core',
    broker=broker,
    backend=backend_result,

    task_serializer='serialize_asyncpg_json',
    result_serializer='serialize_asyncpg_json',
    accept_content=['serialize_asyncpg_json'],
    timezone='UTC',
    enable_utc=True,

    include=[
        'core.bg_tasks.multi_bg_render_data',
        'core.bg_tasks.account_recovery',
        'core.bg_tasks.celery_processing'
    ],
)
celery_bg.conf.result_expires = 600

celery_bg.conf.tasks_queues = [
    Queue(ext_prd_queue, exchange=exchange_mode, routing_key=large_prd_routing_key),
    Queue(mail_queue, exchange=exchange_mode, routing_key=mail_routing_key)
]
