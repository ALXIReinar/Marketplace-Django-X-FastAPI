from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    id: int

class ProductPreviewSchema(ProductBase):
    seller_id: int
    prd_name: str
    cost: Decimal
    remain: int
    path: str
    count_coms: int
    avg_rate: float | None


class SearchSchema(BaseModel):
    text: str


class PaginationSchema(BaseModel):
    limit: int = Field(60)
    offset: int = Field(0, ge=0)

class PaginationSearchSchema(PaginationSchema):
    limit: int = Field(40)

class PaginationFavoriteSchema(PaginationSchema):
    limit: int = Field(20)
