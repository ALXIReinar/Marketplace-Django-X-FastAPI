from fastapi import HTTPException
from pydantic import ValidationError


def parse_raw_schema(raw_obj: str, schema):
    try:
        return schema.model_validate_json(raw_obj)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.errors())

