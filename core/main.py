import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.api.middlewares import LoggingTimeMiddleware, TrafficCounterMiddleware
from core.api import main_router

from core.config_dir.config import get_env_vars


app = FastAPI()
app.include_router(main_router)

"Миддлвари"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"]
)
app.add_middleware(TrafficCounterMiddleware)
app.add_middleware(LoggingTimeMiddleware)



if __name__ == '__main__':
    uvicorn.run('core.main:app', host=get_env_vars().uvicorn_host, port=8000)
