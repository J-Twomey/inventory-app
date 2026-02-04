import argparse
import os
import threading
import time
import webbrowser
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import src.orm_events  # noqa: F401  (import for side-effects)
from src.database import (
    Base,
    get_engine,
)
from src.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=get_engine())
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.mount('/static', StaticFiles(directory='static'), name='static')


def open_browser() -> None:
    time.sleep(0.2)
    webbrowser.open('http://127.0.0.1:8000')


@dataclass
class ProgramArguments:
    dev: bool


def parse_arguments() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        '--dev',
        action='store_true',
        help='Run in development mode with the test DB',
    )
    args = ProgramArguments(**vars(parser.parse_args()))
    return args.dev


def main() -> None:
    dev_mode = parse_arguments()
    if dev_mode:
        os.environ['DEV_MODE'] = '1'
        os.environ['DATABASE_URL'] = 'sqlite:///./db/test6.db'
        reload = True
    else:
        os.environ['DEV_MODE'] = '0'
        os.environ['DATABASE_URL'] = 'sqlite:///./db/prod.db'
        reload = False
    threading.Thread(target=open_browser).start()
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=reload)


if __name__ == '__main__':
    main()
