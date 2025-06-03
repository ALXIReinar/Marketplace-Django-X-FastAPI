import asyncio

from asyncpg import Record
from pydantic import EmailStr

from core.bg_tasks.account_recovery import prepare_mail
from core.bg_tasks.multi_bg_render_data import lvl1_load_data, lvl2_load_data, lvl3_load_data
from core.config_dir.celery_config import celery_bg, ext_prd_queue, large_prd_routing_key, mail_queue, mail_routing_key
from core.config_dir.logger import log_event
from core.utils.anything import Events, hide_log_param

"Расширенная Карточка Товара"
@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl1_render(prd_id: int, front_cached: bool, user_id: int):
    log_event(Events.bg_queue_enter.format(1) + f'prd_id = {prd_id}', level='INFO')
    return asyncio.run(lvl1_load_data(prd_id, front_cached, user_id))

@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl2_render(prd_id: int, seller_id: int):
    log_event(Events.bg_queue_enter.format(2) + f'prd_id = {prd_id}', level='INFO')
    return asyncio.run(lvl2_load_data(prd_id, seller_id))

@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl3_render(prd_id: int):
    log_event(Events.bg_queue_enter.format(3) + f'prd_id = {prd_id}', level='INFO')
    return asyncio.run(lvl3_load_data(prd_id))



"Восстановление Аккаунта(Отправка письма с кодом)"
@celery_bg.task(queue=mail_queue, routing_key=mail_routing_key)
def sending_email_code(email: EmailStr, user: Record, reset_token: str):
    log_event(Events.bg_send_mail + "Постановка в очередь | email: %s; reset_token: %s", hide_log_param(email), reset_token, level='INFO')
    asyncio.run(prepare_mail(email, user, reset_token))
