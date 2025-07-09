import os

from fastapi import APIRouter

from core.config_dir.config import env
from core.data.postgre import PgSqlDep
from core.schemas.test_api_schemas import DBTestNeeds
from core.utils.anything import Tags

router = APIRouter(tags=[Tags.test])



@router.post(env.pg_api_db)
async def db_postman(data: DBTestNeeds, db: PgSqlDep):
    assert os.getenv('MODE') == 'Test' # подумать над доп. условием по IP
    db_ops = {
        'exe': db.conn.execute,
        'fetch': db.conn.fetch,
        'fetchrow': db.conn.fetchrow,
    }

    res = await db_ops[data.method](data.query, *data.args)
    return {'success': True, 'result': res}
