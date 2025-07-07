from contextlib import asynccontextmanager

import uvicorn
from asyncpg import create_pool
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.api.middlewares import LoggingTimeMiddleware, TrafficCounterMiddleware, AuthUxMiddleware
from core.api import main_router
from core.bg_tasks import bg_router

from core.config_dir.config import pool_settings, broadcast, env, get_uvicorn_host



@asynccontextmanager
async def lifespan(web_app):
    web_app.state.pg_pool = await create_pool(**pool_settings)
    await broadcast.connect()
    try:
        yield
    finally:
        await web_app.state.pg_pool.close()
        await broadcast.disconnect()

app = FastAPI(docs_url='/api/docs', openapi_url='/api/openapi.json', lifespan=lifespan)

app.include_router(main_router)
app.include_router(bg_router)

"Миддлвари"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://127.0.0.1:8000"],
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*']
)
app.add_middleware(TrafficCounterMiddleware)
app.add_middleware(AuthUxMiddleware)
app.add_middleware(LoggingTimeMiddleware)


app.mount('/', StaticFiles(directory=f'{env.abs_path}/core/templates', html=True), name='frontend')
app.mount('/', StaticFiles(directory=f'{env.abs_path}/core/templates/images'), name='pic_s')


if __name__ == '__main__':
    uvicorn.run('core.main:app', host=get_uvicorn_host(), port=8000, log_config=None)
