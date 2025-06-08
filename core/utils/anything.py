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
    fake_rT = 'Попытка подмены рефреш_токена'
    fake_rT_or_exp = 'Возможна подмена рефреш_токена/истёк просто'

    bg_product_stage_ = "Карточка товара, степень фона: {} | "
    bg_queue_enter = "Карточка товара, степень фона: {} | Добавление в очередь | "
    bg_call_func =  "Карточка товара, степень фона: {} | Вызов из-под обёртки | "

    bg_send_mail = "Отправка Письма | "

    TEST = "Логи работают!"
    plug = ''



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

def create_log_dirs():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)
    (LOG_DIR / 'info_warning_error').mkdir(exist_ok=True, parents=True)
    (LOG_DIR / 'critical').mkdir(exist_ok=True, parents=True)

def create_debug_log_dir():
    LOG_DIR = Path('logs')
    LOG_DIR.mkdir(exist_ok=True)
    (LOG_DIR / 'debug').mkdir(exist_ok=True, parents=True)


copy_query_PRODUCTS_BY_ID = '''
SELECT p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days, COUNT(c.id) AS count_coms, ROUND(AVG(c.rate), 1) AS avg_rate FROM products p
LEFT JOIN comments c ON c.prd_id = p.id
JOIN images_prdts img ON img.prd_id = p.id AND img.title_img = true
JOIN details_prdts d_p ON d_p.prd_id = p.id 
WHERE p.id IN ({})
AND p.remain > 0
GROUP BY p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days
'''