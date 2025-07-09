import pytest

from contextlib import nullcontext as no_raises

from core.schemas.user_schemas import ValidatePasswSchema
from core.utils.processing_data.raw_fields_to_pydantic import parse_raw_schema
from tests.unit.conftest import get_schemas_and_raw_json


class TestSchemas:
    @pytest.mark.parametrize(
        "passw_string, expect",
        [
            ("Pa$$w0rd", no_raises()),
            ("Pa$$w0d", pytest.raises(ValueError)),
            ("Пароль123@", pytest.raises(ValueError)),
            ("  фыв фыв", pytest.raises(ValueError)),
            ("Pa$$ w0rd", pytest.raises(ValueError)),
            ("Pa$$word", pytest.raises(ValueError)),
        ]
    )
    def test_passw_schema(self, passw_string, expect):
        with expect:
            res = ValidatePasswSchema(passw=passw_string)
            assert res.passw == passw_string, (
                "Валидация пароля не пройдена!"
            )

    @pytest.mark.parametrize("schema, raw_params, expect", get_schemas_and_raw_json())
    def test_schemas_converter(self, schema, raw_params, expect):
        with expect:
            assert isinstance(parse_raw_schema(raw_params, schema), schema), (
                'Строка-json Не перевелась в Pydantic-Схему!'
            )
