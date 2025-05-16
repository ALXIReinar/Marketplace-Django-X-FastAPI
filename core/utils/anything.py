from dataclasses import dataclass

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
    users = 'Пользователи'
    products = 'Товары'

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


def hide_log_param(param, start=3, end=8):
    return param[:start] + '*' * len(param[start:-end-1]) + param[-end:]