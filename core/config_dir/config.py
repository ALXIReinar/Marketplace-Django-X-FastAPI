import os

from dotenv import load_dotenv
load_dotenv()

PG_USER=os.getenv('PG_USER')
PG_PASSWORD=os.getenv('PG_PASSWORD')
PG_DB=os.getenv('PG_DB')
PG_HOST=os.getenv('PG_HOST')
PG_PORT=os.getenv('PG_PORT')

UVICORN_HOST=os.getenv('UVICORN_HOST')
UVICORN_PORT=os.getenv('UVICORN_PORT')