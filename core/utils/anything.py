from dataclasses import dataclass
from pathlib import Path

methods = {
    "DELETE": "\033[91m DELETE \033[0m",
    "GET": "\033[92m GET \033[0m",
    "HEAD": "\033[92m HEAD \033[0m",
    "OPTIONS": "\033[93m OPTIONS \033[0m",
    "PATCH": "\033[94m PATCH \033[0m",
    "POST": "\033[94m POST \033[0m",
    "PUT": "\033[93m PUT \033[0m"
}

@dataclass
class Tags:
    users = 'Пользователи👥'
    products = 'Товары'
    favorites = 'Избранное❤️'
    orders = 'Заказы'
    elastic_products = 'Товары *Elastic🔎*'
    celery_bg = 'Celery Фон🥬🐇'
    crons = 'Отложенные задачи🕟'
    chat = 'Мессенджер💬'
    file_reader = 'Файловое Хранилище🗂'
    test = 'Тестовые ручки🧪'

@dataclass
class Events:
    registr_user = 'Юзер зарегистрировался'
    unluck_registr_user = 'Юзер не смог зарегистрироваться'
    unluck_login_user = 'Юзер не смог войти в аккаунт'

    white_list_url = 'Пройдено без проверки Авторизации'
    long_response = 'Долгий ответ'
    lim_requests_ip = "Превышен лимит запросов"

    new_aT = "Выпущен аксес_токен"
    fake_aT_try = "Попытка подмены аксес_токена"
    fake_wT_try = "Попытка подмены ws_токена | WebSocket Auth | "
    fake_rT = 'Попытка подмены рефреш_токена'
    fake_wT = 'Попытка подмены ws_токена'
    fake_rT_or_exp = 'Возможна подмена рефреш_токена/истёк просто'

    bg_product_stage_ = "Карточка товара, степень фона: {} | "
    bg_queue_enter = "Карточка товара, степень фона: {} | Добавление в очередь | "
    bg_call_func =  "Карточка товара, степень фона: {} | Вызов из-под обёртки | "

    bg_send_mail = "Отправка Письма | "

    periodic_cron = 'Крона запущена | '
    cron_completed = 'Регулярная таска выполнена | '

    TEST = "Логи работают!"
    plug = ''

@dataclass
class TokenTypes:
    access_token: str = 'aT'
    refresh_token: str = 'rT'
    ws_token: str = 'wT'

token_types = {
    'access_token': 'aT',
    'refresh_token': 'rT',
    'ws_token': 'wT'
}

mail_ptn_forget_password_HTML='''
<!DOCTYPE html>
    <html lang="ru">
    <head><meta charset="UTF-8" /></head>
    <body>
      <h2>Здравствуйте {}!</h2>
      <p>Вы запросили восстановление пароля на <em>Pied Market</em>.</p>
      <p>Ваш код подтверждения:</p>
      <h1 style="color:#2c3e50;">{}</h1>
      <p>Код действует 10 минут.</p>
      <p>Если это были не вы — просто проигнорируйте письмо.</p>
      <hr>
      <p>С уважением, команда <strong>Pied Market</strong></p>
    </body>
    </html>
'''

mail_ptn_forget_password_TEXT = '''
Тема: Восстановление пароля на Pied Market

Здравствуйте {}!

Вы запросили восстановление пароля на Pied Market. Ваш код подтверждения:

🔐 {}

Пожалуйста, введите этот код в течение 10 минут, чтобы подтвердить свой аккаунт.

Если это не Вы, проигнорируйте это письмо. Ваш аккаунт останется в безопасности.

С уважением,  
Команда Pied Market
'''

def hide_log_param(param, start=3, end=8):
    return param[:start] + '*' * len(param[start:-end-1]) + param[-end:]

def cut_log_param(param, compression_times=20):
    return param[len(param)//compression_times:] + '...'

def create_log_dirs():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)
    (LOG_DIR / 'info_warning_error').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'critical').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'debug').mkdir(exist_ok=True, parents=True)

def create_bg_files_dir():
    BG_FILES_DIR = Path('user_files_bg_dumps')
    BG_FILES_DIR.mkdir(exist_ok=True)
