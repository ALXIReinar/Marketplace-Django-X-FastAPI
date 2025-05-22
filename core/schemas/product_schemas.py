from pydantic import BaseModel, Field
from typing_extensions import Optional


class ProductBase(BaseModel):
    id: Optional[int]

class ProductPreviewSchema(ProductBase):
    seller_id: int
    prd_name: str
    category: str
    path: str
    rate: int


class SearchSchema(BaseModel):
    text: str


class PaginationSchema(BaseModel):
    limit: int = Field(60)
    offset: int = Field(0, ge=0)

class PaginationSearchSchema(PaginationSchema):
    limit: int = Field(40)
