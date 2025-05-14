from typing import Annotated

from fastapi.params import Depends

from core.schemas.product_schemas import PaginationSchema


PagenDep = Annotated[PaginationSchema, Depends(PaginationSchema)]