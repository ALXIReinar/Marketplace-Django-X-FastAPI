import requests
from asyncpg import Record
from pydantic import EmailStr

from core.config_dir.celery_config import celery_bg, ext_prd_queue, large_prd_routing_key, mail_queue, mail_routing_key, \
    bg_link, file_queue, file_routing_key
from core.config_dir.logger import log_event
from core.utils.anything import Events, hide_log_param

"Расширенная Карточка Товара"
@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl1_render(prd_id: int, front_cached: bool, user_id: int):
    log_event(Events.bg_queue_enter.format(1) + f'prd_id = {prd_id}', level='INFO')
    return requests.post(
        f'{bg_link}/ext_prd/lvl1', json={'prd_id': prd_id, 'front_cached': front_cached, 'user_id': user_id}).json()

@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl2_render(prd_id: int, seller_id: int):
    log_event(Events.bg_queue_enter.format(2) + f'prd_id = {prd_id}', level='INFO')
    return requests.post(
        f'{bg_link}/ext_prd/lvl2', json={'prd_id': prd_id, 'seller_id': seller_id}).json()

@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl3_render(prd_id: int):
    log_event(Events.bg_queue_enter.format(3) + f'prd_id = {prd_id}', level='INFO')
    return requests.post(
        f'{bg_link}/ext_prd/lvl3', json={'prd_id': prd_id}).json()


"Восстановление Аккаунта(Отправка письма с кодом)"
@celery_bg.task(queue=mail_queue, routing_key=mail_routing_key)
def sending_email_code(email: EmailStr, user: Record, reset_token: str):
    log_event(Events.bg_send_mail + "Постановка в очередь | email: %s; reset_token: %s", hide_log_param(email), reset_token, level='INFO')
    return requests.post(
        f'{bg_link}/email_check', json={'email': email,'user': user,'reset_token': reset_token})


"Загрузка файла в облако"
@celery_bg.task(bind=True, max_retries=5, default_retry_delay=60, queue=file_queue, routing_key=file_routing_key)
def bg_s3_upload(self, file_path: str):
    try:
        response = requests.put(f'{bg_link}/s3_upload/saving', params={'file_path': file_path})
        response.raise_for_status()
    except Exception as exc:
        log_event('Ретрай сохранения в С3 | file: %s | %s', file_path, exc, level='WARNING')
        raise self.retry(exc=exc)


"Периодические Задачи"
@celery_bg.task()
def run_rT_cleaner():
    requests.delete(f'{bg_link}/crons/flush_refresh-tokens').json()

@celery_bg.task()
def run_messages_cleaner():
    requests.delete(f'{bg_link}/crons/delete_chat-messages').json()
