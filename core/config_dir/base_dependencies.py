from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi.params import Depends

from core.config_dir.config import get_elastic_client
from core.schemas.product_schemas import PaginationSchema, PaginationSearchSchema, PaginationFavoriteSchema, PaginationChatSchema


PagenDep = Annotated[PaginationSchema, Depends(PaginationSchema)]
PagenSearchDep = Annotated[PaginationSearchSchema, Depends(PaginationSearchSchema)]
PagenFavoriteDep = Annotated[PaginationFavoriteSchema, Depends(PaginationFavoriteSchema)]
PagenChatDep = Annotated[PaginationChatSchema, Depends(PaginationChatSchema)]
ElasticDep = Annotated[AsyncElasticsearch, Depends(get_elastic_client)]