"""FastAPI 应用入口。"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.routers.questions import router as question_router
from app.seed import seed_questions


def _cors_origins() -> list[str]:
    """从环境变量读取允许的前端来源，多个来源使用逗号分隔。"""
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用启动时建表并初始化演示题库。"""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_questions(db)
    yield


app = FastAPI(
    title="Python 刷题小站 API",
    version="1.0.0",
    description="Python 基础单选题的抽题、判题和录入接口。",
    lifespan=lifespan,
)

origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(question_router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"message": "Python 刷题小站 API", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}

