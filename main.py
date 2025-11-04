from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from database.init_db import init_db
from routers.auth import router as auth_router
from routers.films import router as film_router
from routers.halls import router as hall_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(film_router)
app.include_router(hall_router)


@app.get("/healthcheck")
async def healthcheck():
    return "Service live!"


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
