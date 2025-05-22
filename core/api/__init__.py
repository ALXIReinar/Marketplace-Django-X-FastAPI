from fastapi import APIRouter

from .users import router as user_router
from .products import router as product_router
from .elastic_search import router as search_router

main_router = APIRouter()

main_router.include_router(user_router)
main_router.include_router(product_router)
main_router.include_router(search_router)