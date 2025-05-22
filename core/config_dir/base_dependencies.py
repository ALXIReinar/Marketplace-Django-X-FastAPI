from typing import Annotated

from fastapi.params import Depends

from core.schemas.product_schemas import PaginationSchema, PaginationSearchSchema

PagenDep = Annotated[PaginationSchema, Depends(PaginationSchema)]
PagenSearchDep = Annotated[PaginationSearchSchema, Depends(PaginationSearchSchema)]