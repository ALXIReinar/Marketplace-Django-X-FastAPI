from core.config_dir.config import env

apis_dont_need_auth = {
    '/',

    '/api/users/sign_up',
    '/api/users/login',

}

white_list_postfix = ['.html', '.css', '.png', '.jpg', '.ico', '.json']

white_list_prefix_cookies = ['/products', '/favorites', '/orders', '/login', '/sign_up']

allowed_ips = {'127.0.0.1', 'localhost', env.internal_host, 'pied_market', 'pg_db_pied_market', 'redis_pied_market',
               'es01', 'rabbitmq', 'celery_worker', 'smtp_service'}