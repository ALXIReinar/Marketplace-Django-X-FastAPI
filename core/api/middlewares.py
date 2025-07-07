import time
from collections.abc import Callable
from datetime import datetime


from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from starlette.responses import JSONResponse

from core.config_dir.logger import log_event
from core.data.postgre import set_connection, PgSql
from core.data.redis_storage import get_redis_connection
from core.utils.anything import Events
from core.config_dir.urls_middlewares import white_list_prefix_NO_COOKIES, allowed_ips
from core.utils.processing_data.ip_taker import get_client_ip
from core.utils.processing_data.jwt_processing import reissue_aT
from core.utils.processing_data.jwt_utils.jwt_encode_decode import get_jwt_decode_payload


class TrafficCounterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_limit: int = 0, ttl_limit: int = 0):
        super().__init__(app=app)
        self.limit = requests_limit
        self.ttl = ttl_limit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ip = get_client_ip(request)
        request.state.client_ip = ip
        if ip in allowed_ips:
            return await call_next(request)

        async with get_redis_connection() as redis:
            request_counter = await redis.get(ip)
            if request_counter and int(request_counter.decode()) >= self.limit:
                log_event('Отброшен за превышение обращений!', level='CRITICAL')
                return JSONResponse(status_code=429, content={'message': 'Превышен лимит обращений. Попробуйте позже'})
            elif request_counter is None:
                await redis.set(ip, value=1, ex=self.ttl)
            else:
                to_disappear = await redis.ttl(ip)
                await redis.set(ip, value=int(request_counter.decode()) + 1, ex=to_disappear)
        return await call_next(request)


class LoggingTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        end = time.perf_counter() - start
        if end > 7.0:
            log_event(Events.long_response + f' {end: .4f}', request=request, level='WARNING')
        return response

class AuthUxMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        now = datetime.utcnow()
        request.state.user_id = 1
        request.state.session_id = '1'

        url = request.url.path
        ip = request.state.client_ip

        "Веб-адреса или запросы Сервера"
        if not url.startswith('/api') or ip in allowed_ips:
            log_event(Events.white_list_url, request=request)
            return await call_next(request)
        "Не нуждаются в авторизации, Если нет кук"
        if not request.cookies and any(tuple(url.startswith(prefix) for prefix in white_list_prefix_NO_COOKIES)):
            log_event(Events.white_list_url, request=request, level='WARNING')
            return await call_next(request)


        encoded_access_token = request.cookies.get('access_token')
        if (access_token:= get_jwt_decode_payload(encoded_access_token)) == 401:
            # невалидный аксес_токен
            log_event(Events.fake_aT_try, request=request, level='CRITICAL')
            return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
        if datetime.utcfromtimestamp(access_token['exp']) < now:
            # аксес_токен ИСТЁК
            "процесс выпуска токена"
            pool = await set_connection()
            async with pool.acquire() as conn:
                db = PgSql(conn)
                refresh_token = request.cookies.get('refresh_token')
                new_token = await reissue_aT(access_token, refresh_token, db)
            if new_token == 401:
                # рефреш_токен НЕ ВАЛИДЕН
                log_event(Events.fake_rT + f"| s_id: {access_token.get('s_id', '')}; user_id: {access_token.get('sub', '')}", request=request, level='CRITICAL')
                return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
            request.cookies['access_token'] = new_token

        request.state.user_id = int(access_token['sub'])
        request.state.session_id = access_token['s_id']
        return await call_next(request)
