import pytest
from unittest.mock import AsyncMock

from core.schemas.user_schemas import TokenPayloadSchema
from core.utils.processing_data.jwt_utils.jwt_encode_decode import get_jwt_decode_payload
from core.utils.processing_data.jwt_utils.jwt_factory import add_ttl_limit, issue_token
from tests.unit.conftest import get_token_list


class TestJWT:
    @pytest.mark.parametrize(
        "token_type, token_ttl_config",
        get_token_list(with_ttl=True)
    )
    def test_ttl_tokens(self, token_type: str, token_ttl_config):
        payload = {}
        finally_payload = add_ttl_limit(payload, token_type)
        assert 'iat' in finally_payload and 'exp' in finally_payload
        assert (finally_payload['exp'] - finally_payload['iat']).total_seconds() == token_ttl_config.total_seconds()

    @pytest.mark.parametrize(
        'token',
        get_token_list(with_ttl=False)
    )
    def test_content_token(self, token):
        payload_object = {'sub': '0', 's_id': '0'}
        finally_payload = add_ttl_limit(payload_object, token)
        assert payload_object is finally_payload

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "token",
        get_token_list(with_ttl=False)
    )
    async def test_equal_payload_token(self, token):
        payload = {'some': 'thing', 'sub': '0'}
        mock_db = AsyncMock()
        mock_db.auth.make_session.return_value = None

        encoded_token = await issue_token(
            payload,
            token,
            db=mock_db,
            session_id='pytest_session',
            client=TokenPayloadSchema(user_agent='pytest', ip='pytest.host', id=0)
        )
        if token == 'refresh_token':
            assert len(encoded_token) == 60
        else:
            decoded_token = get_jwt_decode_payload(encoded_token, False)
            assert payload['sub'] == decoded_token.get('sub')

