apis_dont_need_auth = {
    '/',
    '/api/users/sign_up',
    '/api/users/login',

}

white_list_postfix = ['.html', '.css', '.png', '.jpg', '.ico', '.json']

white_list_prefix_cookies = ['/products', '/favorites', '/orders', '/login', '/sign_up']

allowed_ips = {
    '127.0.0.1',
    '172.25.0.1',
    '172.25.0.14', # селери воркер
    '172.25.0.15', # селери бит
    '172.25.0.19'  # web-app(fastapi)
}

trusted_proxies = {'127.0.0.1', '172.25.0.1',}
