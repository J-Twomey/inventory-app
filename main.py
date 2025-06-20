import threading
import time
import webbrowser
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.database import (
    Base,
    engine,
)
from src.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.mount('/static', StaticFiles(directory='static'), name='static')


def open_browser() -> None:
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:8000')


def main() -> None:
    threading.Thread(target=open_browser).start()
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)


if __name__ == '__main__':
    main()
