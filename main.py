from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.init_db import init_db
from routers.auth import router as auth_router
from routers.films import router as film_router
from routers.halls import router as hall_router
from routers.sessions import router as session_router
from routers.bookings import router as booking_router
from routers.views_router import router as views_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(film_router)
app.include_router(hall_router)
app.include_router(session_router)
app.include_router(booking_router)
app.include_router(views_router)

origins = [
    "http://localhost:8080",
    "http://localhost:8000",
    "http://localhost:5173",

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthcheck")
async def healthcheck():
    return "Service live!"



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
