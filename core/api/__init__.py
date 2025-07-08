from celery.result import AsyncResult
from fastapi import APIRouter

from .users import router as user_router
from .products import router as product_router
from .elastic_search import router as search_router
from .favorites import router as favorite_router
from .orders import router as order_router
from ..utils.anything import Tags
from .websocket_messenger import router as messenger_router

main_router = APIRouter()

main_router.include_router(user_router)
main_router.include_router(product_router)
main_router.include_router(search_router)
main_router.include_router(favorite_router)
main_router.include_router(order_router)
main_router.include_router(messenger_router)



@main_router.get('/api/public/bg_tasks/{task_id}', tags=[Tags.celery_bg])
async def get_bg_task(task_id: str):
    task = AsyncResult(task_id)
    if not task.ready():
        return {'success': False}
    return {'success': True, 'result': task.result}