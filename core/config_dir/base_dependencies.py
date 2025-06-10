from typing import Annotated

from fastapi.params import Depends

from core.schemas.product_schemas import PaginationSchema, PaginationSearchSchema, PaginationFavoriteSchema, PaginationChatSchema

PagenDep = Annotated[PaginationSchema, Depends(PaginationSchema)]
PagenSearchDep = Annotated[PaginationSearchSchema, Depends(PaginationSearchSchema)]
PagenFavoriteDep = Annotated[PaginationFavoriteSchema, Depends(PaginationFavoriteSchema)]
PagenChatDep = Annotated[PaginationChatSchema, Depends(PaginationChatSchema)]
