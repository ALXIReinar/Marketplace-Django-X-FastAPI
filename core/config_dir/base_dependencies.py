from typing import Annotated

from fastapi.params import Depends

from core.schemas.product_schemas import PaginationSchema, PaginationSearchSchema, PaginationFavoriteSchema, PaginationChatSchema
from core.schemas.chat_schema import PaginationChatMessSchema

PagenDep = Annotated[PaginationSchema, Depends(PaginationSchema)]
PagenSearchDep = Annotated[PaginationSearchSchema, Depends(PaginationSearchSchema)]
PagenFavoriteDep = Annotated[PaginationFavoriteSchema, Depends(PaginationFavoriteSchema)]
PagenChatDep = Annotated[PaginationChatSchema, Depends(PaginationChatSchema)]
PagenChatMessDep = Annotated[PaginationChatMessSchema, Depends(PaginationChatMessSchema)]