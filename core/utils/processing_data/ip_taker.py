from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config_dir.urls_middlewares import trusted_proxies


def get_client_ip(request: Request | WebSocket):
    xff = request.headers.get('X-Forwarded-For')
    ip = xff.split(',')[0].strip() if (
            xff and request.client.host in trusted_proxies
    ) else request.client.host
    return ip