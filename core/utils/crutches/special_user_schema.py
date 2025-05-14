from copy import deepcopy
from typing import Any, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, create_model, Field
from pydantic.fields import FieldInfo

# UNUSED
# UNUSED
# UNUSED
# UNUSED
# UNUSED
# UNUSED
class User(BaseModel):
  id: int = Field(1)


def make_field_optional(field: FieldInfo, default: Any = None) -> Tuple[Any, FieldInfo]:
  new = deepcopy(field)
  new.default = default
  new.annotation = Optional[field.annotation]  # type: ignore
  return (new.annotation, new)


BaseModelT = TypeVar('BaseModelT', bound=BaseModel)

def make_partial_model(model: Type[BaseModelT]) -> Type[BaseModelT]:
  return create_model(  # type: ignore
    f'Partial{model.__name__}',
    __base__=User,
    __module__=User.__module__,
    **{
        field_name: make_field_optional(field_info)
        for field_name, field_info in User.model_fields.items()
    }
    )


UserBaseDangerous = make_partial_model(User)
