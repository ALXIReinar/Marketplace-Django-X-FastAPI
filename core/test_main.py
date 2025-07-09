from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from core.api import main_router
from core.bg_tasks import bg_router
from core.config_dir.config import env
from core.main import lifespan
from tests.conftest import SimpleAuthMiddlewareTest

test_app = FastAPI(lifespan=lifespan)

test_app.include_router(main_router)
test_app.include_router(bg_router)

test_app.add_middleware(SimpleAuthMiddlewareTest)


test_app.mount('/', StaticFiles(directory=f'{env.abs_path}/core/templates', html=True), name='frontend')
test_app.mount('/', StaticFiles(directory=f'{env.abs_path}/core/templates/images'), name='pic_s')
