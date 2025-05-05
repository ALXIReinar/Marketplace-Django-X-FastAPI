import asyncio
import uvicorn

from core.config_dir.config import UVICORN_HOST, UVICORN_PORT


async def main():
    # code-initialize another services

    uvicorn.run('main:app', host=UVICORN_HOST, port=UVICORN_PORT)



if __name__ == '__main__':
    asyncio.run(main())
