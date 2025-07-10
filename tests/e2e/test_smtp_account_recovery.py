import asyncio

import pytest

from core.data.redis_storage import get_redis_connection


@pytest.mark.parametrize(
    'email',
    [
        'non_exists@gmail.com',
        'test_user1@gmail.com'
    ]
)
@pytest.mark.asyncio
async def test_account_recovery(prod_ac, xff_ip, email):
    response_frgt_passw = await prod_ac.post('/api/public/users/passw/forget_passw', json={'email': email}, headers=xff_ip)
    reset_token = response_frgt_passw.json()['reset_token']

    await asyncio.sleep(5)
    async with get_redis_connection() as redis:
        reset_code_init = await redis.get(reset_token)
        if reset_code_init:
            await redis.set(2, 111_111)
        else:
            assert reset_code_init is None
            return

    comparing = await prod_ac.get(
        '/api/public/users/passw/compare_confirm_code',
        params={'reset_token': reset_token, 'code': 111_111},
        headers=xff_ip
    )
    assert comparing.status_code == 200

    new_password = 'l0giN-true'
    response_new_passw = await prod_ac.put(
        '/api/public/users/passw/set_new_passw',
        json={'reset_token': reset_token, 'passw': new_password},
        headers=xff_ip
    )
    assert response_new_passw.status_code == 200

    try_log_in = await prod_ac.post('/api/public/users/login', json={'email': email, 'passw': new_password}, headers=xff_ip)
    assert try_log_in.json()['success'] == True and len(try_log_in.cookies) == 2
