from fastapi import APIRouter

from .account_recovery import router as email_router
from .multi_bg_render_data import router as ext_router
from .regular_crons import router as cron_router

bg_router = APIRouter()

bg_router.include_router(email_router)
bg_router.include_router(ext_router)
bg_router.include_router(cron_router)
