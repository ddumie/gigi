from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base
from backend.api.router import api_router

app = FastAPI(title="GIGI - 세대를 잇는 건강한 응원")

# API 라우터 등록
app.include_router(api_router)

# 프론트엔드 정적 파일 서빙
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)