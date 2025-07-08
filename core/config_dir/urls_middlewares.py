white_list_prefix_NO_COOKIES = [
    '/api/products',
    '/api/public',
    '/api/favorites',
    '/api/orders',
]

allowed_ips = {
    '127.0.0.1',
    '172.25.0.1',
    '172.25.0.14', # селери воркер
    '172.25.0.15', # селери бит
    '172.25.0.19'  # web-app(fastapi)
}

trusted_proxies = {'127.0.0.1', '172.25.0.1',}
