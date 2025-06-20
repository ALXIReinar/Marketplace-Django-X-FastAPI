from fastapi import APIRouter

from .account_recovery import router as email_router
from .multi_bg_render_data import router as ext_router
from .regular_crons import router as cron_router
from .cloud_file_downloader import router as file_manager_router
from ..utils.anything import Tags

bg_router = APIRouter(prefix='/api/bg_tasks', tags=[Tags.celery_bg])

bg_router.include_router(email_router)
bg_router.include_router(ext_router)
bg_router.include_router(cron_router)
bg_router.include_router(file_manager_router)
