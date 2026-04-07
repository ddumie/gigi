from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.database import Base, engine, load_model_modules

app = FastAPI(title="GIGI - 세대를 잇는 건강한 응원")

app.include_router(api_router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
def on_startup():
    load_model_modules()
    Base.metadata.create_all(bind=engine)
