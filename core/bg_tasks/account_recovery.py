from random import randint
from email.message import EmailMessage

from fastapi import APIRouter
from pydantic import EmailStr
from starlette.requests import Request

from core.config_dir.config import smtp, env
from core.config_dir.logger import log_event
from core.data.redis_storage import RedisDep
from core.schemas.user_schemas import RecoveryPrepareSchema
from core.utils.anything import mail_ptn_forget_password_TEXT, mail_ptn_forget_password_HTML, hide_log_param

router = APIRouter(prefix='/public/bg_tasks')



def send_confirm_code(to: EmailStr | str, user_name: str, code: str):
    receiver = '' if user_name == 'Пользователь Pied Market' else f', {user_name}'
    content = mail_ptn_forget_password_TEXT.format(receiver, code)

    msg = EmailMessage()
    msg['To'], msg['From'], msg['Subject'] = to, env.mail_sender, 'Восстановление пароля на Pied Market'
    msg.set_content(content)
    msg.add_alternative(mail_ptn_forget_password_HTML.format(receiver, code), subtype='html')
    return msg

@router.post('/email_check')
async def prepare_mail(recovery_obj: RecoveryPrepareSchema, request: Request, redis: RedisDep):
    if recovery_obj.user:
        confirm_code = str(randint(100_000, 999_999))
        await redis.set(recovery_obj.reset_token, recovery_obj.user['id'], ex=600)
        await redis.set(str(recovery_obj.user['id']), confirm_code, ex=630)

        msg = send_confirm_code(recovery_obj.email, recovery_obj.user['name'], confirm_code)
        async with smtp as smtp_conn:
            await smtp_conn.send_message(msg)
        log_event(f"Отправка Письма | email: %s; user_name: %s; code: %s",
                  hide_log_param(recovery_obj.email), env.mail_sender, confirm_code, request=request)
        return {'success': True, 'message': 'Эмайл с кодом отправлен'}
    log_event('Пользователь ввёл несуществующую почту: %s', recovery_obj.email, request=request, level='WARNING')
    return {'success': False, 'message': f'{recovery_obj.email} - нет в БД'}
