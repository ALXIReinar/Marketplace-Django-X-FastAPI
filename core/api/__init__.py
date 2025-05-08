from fastapi import APIRouter

from .products import router as product_router


main_router = APIRouter()

main_router.include_router(product_router)