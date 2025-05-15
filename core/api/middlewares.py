import time
from collections.abc import Callable
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from starlette.responses import JSONResponse

from core.config_dir.logger import methods, apis_dont_need_auth
from core.db_data.postgre import PgSqlDep
from core.utils.processing_data.jwt_processing import reissue_aT
from core.utils.processing_data.jwt_utils.jwt_encode_decode import get_jwt_decode_payload


class TrafficCounterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Подрубить Редис, чтобы на каждый айпи расставлять счётчик запросов
        Псевдо-код:
        ip = request.client.host
        request_counter = redis.get(ip)
        if request_counter and request_counter > 250:
            return JSONResponse(status_code=429, content={'message': 'Превышен лимит обращений за 5 минут. Попробуйте позже'})
        elif request_counter is None:
            redis.set(ip, value=0, ttl=300)

        request_counter += 1
        """
        return await call_next(request)


class LoggingTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        end = time.perf_counter() - start
        print(f"{methods[request.method]}| {request.url.path} | {end:.4f}")
        # logger.info(f"end")
        return response

class AuthUxMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, db: PgSqlDep):
        super().__init__(app)
        self.db = db

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        now = datetime.utcnow()
        if request.url.path in apis_dont_need_auth:
            return await call_next(request)

        encoded_access_token = request.cookies.get('access_token')
        if (access_token:= get_jwt_decode_payload(encoded_access_token)) == 401:
            return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})

        if datetime.utcfromtimestamp(access_token['exp']) < now:
            # аксес_токен ИСТЁК
            refresh_token = request.cookies.get('refresh_token')
            new_token = await reissue_aT(access_token, refresh_token, self.db)
            if new_token == 401:
                # рефреш_токен НЕ ВАЛИДЕН
                return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
            request.cookies['access_token'] = new_token

        request.state.user_id = int(access_token['sub'])
        request.state.session_id = access_token['s_id']
        return await call_next(request)

















