import uvicorn
from asyncpg import create_pool
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.api.middlewares import LoggingTimeMiddleware, TrafficCounterMiddleware, AuthUxMiddleware
from core.api import main_router
from core.bg_tasks import bg_router

from core.config_dir.config import app, pool_settings, broadcast, env

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

@app.on_event('startup')
async def startup():
    app.state.pg_pool = await create_pool(**pool_settings)
    await broadcast.connect()

@app.on_event('shutdown')
async def shutdown():
    await app.state.pg_pool.close()
    await broadcast.disconnect()

app.mount('/', StaticFiles(directory=f'{env.abs_path}/core/templates', html=True), name='frontend')
app.mount('/', StaticFiles(directory=f'{env.abs_path}/core/templates/images'), name='pic_s')


if __name__ == '__main__':
    uvicorn.run('core.main:app', host=env.uvicorn_host_docker if env.dockerized else env.uvicorn_host, port=8000, log_config=None)
