import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.api.middlewares import LoggingTimeMiddleware, TrafficCounterMiddleware, AuthUxMiddleware
from core.api import main_router

from core.config_dir.config import get_env_vars, app
from core.db_data.postgre import PgSqlDep

app.include_router(main_router)

"Миддлвари"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://127.0.0.1:8000"],
    allow_methods=['GET', 'POST'],
    allow_headers=['*']
)
# app.add_middleware(TrafficCounterMiddleware)
app.add_middleware(AuthUxMiddleware, db=PgSqlDep)
app.add_middleware(LoggingTimeMiddleware)


app.mount('/', StaticFiles(directory=f'{get_env_vars().abs_path}/core/templates', html=True), name='frontend')
app.mount('/', StaticFiles(directory=f'{get_env_vars().abs_path}/core/templates/images'), name='pic_s')


if __name__ == '__main__':
    uvicorn.run('core.main:app', host=get_env_vars().uvicorn_host, port=8000, log_config=None)
