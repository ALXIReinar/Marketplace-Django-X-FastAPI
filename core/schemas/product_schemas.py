from decimal import Decimal

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    prd_id: int

class ProductPreviewSchema(ProductBase):
    prd_name: str
    cost: Decimal
    remain: int
    path: str
    count_coms: int
    avg_rate: float | None


class SearchSchema(BaseModel):
    text: str


class LVL1ExtendedPrdSchema(ProductBase):
    front_cached: bool
    user_id: int

class LVL2ExtendedPrdSchema(ProductBase):
    seller_id: int


class PaginationSchema(BaseModel):
    limit: int = Field(60)
    offset: int = Field(0, ge=0)

class PaginationSearchSchema(PaginationSchema):
    limit: int = Field(40)

class PaginationFavoriteSchema(PaginationSchema):
    limit: int = Field(20)

class PaginationChatSchema(PaginationSchema):
    limit: int = Field(30)
