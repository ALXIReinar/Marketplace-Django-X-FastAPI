from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError


def parse_schema(raw_obj: str, schema):
    try:
        return schema.parse_raw(raw_obj)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())
