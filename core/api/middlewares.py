import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from core.config_dir.logger import methods


class TrafficCounterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Подрубить Редис, чтобы на каждый айпи расставлять счётчик запросов
        Псевдо-код:
        ip = request.client.host
        request_counter = redis.get(ip)
        if request_counter and request_counter > 250:
            return Response(status_code=429, content='Превышен лимит обращений за 5 минут. Попробуйте позже')
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