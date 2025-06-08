from random import randint
from email.message import EmailMessage

from asyncpg import Record
from pydantic import EmailStr

from core.config_dir.config import smtp, env
from core.config_dir.logger import log_event
from core.data.redis_storage import get_redis_connection
from core.utils.anything import mail_ptn_forget_password_TEXT, mail_ptn_forget_password_HTML, hide_log_param


async def send_confirm_code(to: EmailStr | str, user_name: str, code: str):
    receiver = '' if user_name == 'Пользователь Pied Market' else f', {user_name}'
    content = mail_ptn_forget_password_TEXT.format(receiver, code)

    msg = EmailMessage()
    msg['To'], msg['From'], msg['Subject'] = to, env.mail_sender, 'Восстановление пароля на Pied Market'
    msg.set_content(content)
    msg.add_alternative(mail_ptn_forget_password_HTML.format(receiver, code), subtype='html')

    log_event(f"Отправка Письма | email: %s; user_name: %s; code: %s", hide_log_param(to), receiver, code)
    async with smtp:
        await smtp.send_message(msg)


async def prepare_mail(email: EmailStr, user: Record, reset_token: str):
    if user:
        confirm_code = str(randint(100_000, 999_999))
        async with get_redis_connection() as redis:
            await redis.set(reset_token, user['id'], ex=600)
            await redis.set(str(user['id']), confirm_code, ex=630)
        await send_confirm_code(email, user['name'], confirm_code)
