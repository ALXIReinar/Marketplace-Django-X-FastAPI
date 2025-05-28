from celery import Celery
from kombu import Exchange, Queue

from core.config_dir.config import env



broker = env.celery_broker_url if env.dockerized else f"pyamqp://{env.rabbitmq_user}@localhost//"
backend_result = env.celery_result_backend if env.dockerized else f"redis://localhost:{env.redis_port}/0"

ext_prd_queue = 'extended_product_card_queue'
ex_meth = 'ex_method'
large_prd_routing_key = 'prd_routing_key'


celery_bg = Celery(
    'core',
    broker=broker,
    backend=backend_result,
    include=[
        'core.bg_tasks.multi_bg_render_data',
        'core.bg_tasks.celery_processing'
    ]
)
celery_bg.conf.result_expires = 600

celery_bg.conf.tasks_queues = [
    Queue(ext_prd_queue, exchange=Exchange(ex_meth, type='direct'), routing_key=large_prd_routing_key)
]