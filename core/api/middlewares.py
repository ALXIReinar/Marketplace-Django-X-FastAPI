import time
from collections.abc import Callable
from datetime import datetime


from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from starlette.responses import JSONResponse

from core.config_dir.logger import log_event
from core.data.postgre import init_pool
from core.utils.anything import Events
from core.config_dir.urls_middlewares import apis_dont_need_auth, white_list_postfix, white_list_prefix_cookies, \
    white_list_prefix
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
        # log_event(Events.lim_requests_ip, request,
        #           user_id=request.state.user_id if hasattr(request.state, 'user_id') else '',
        #           s_id=request.state.session_id if hasattr(request.state, 'session_id') else '')
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
        url = request.url.path
        request.state.user_id = 1
        request.state.session_id = '1'
        if (url in apis_dont_need_auth or
            any(tuple(url.endswith(postfix) for postfix in white_list_postfix)) or

            any(tuple(url.startswith(prefix) for prefix in white_list_prefix)) or

          (any(tuple(url.startswith(prefix) for prefix in white_list_prefix_cookies)) and not request.cookies)
        ):

            log_event(Events.white_list_url + " | cookies: %s", request.cookies.keys(), request=request, level='WARNING')
            return await call_next(request)



        encoded_access_token = request.cookies.get('access_token')
        if (access_token:= get_jwt_decode_payload(encoded_access_token)) == 401:
            # невалидный аксес_токен
            log_event(Events.fake_aT_try, request=request, level='CRITICAL')
            return JSONResponse(status_code=401, content={'message': 'Нужна повторная аутентификация'})
        if datetime.utcfromtimestamp(access_token['exp']) < now:
            # аксес_токен ИСТЁК


            "процесс выпуска токена"
            async with init_pool() as db:
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

















