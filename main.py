from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from database.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/healthcheck")
async def healthcheck():
    return "Service live!"

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)