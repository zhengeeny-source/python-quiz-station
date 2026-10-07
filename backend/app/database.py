"""数据库连接与会话管理。"""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 本地开发可直接复制 .env.example 为 .env；云平台仍由环境变量覆盖。
load_dotenv()


def _database_url() -> str:
    """读取数据库地址，并兼容部分平台提供的 mysql:// 地址。"""
    url = os.getenv("DATABASE_URL", "sqlite:///./python_quiz.db")
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)
    return url


DATABASE_URL = _database_url()

engine_options: dict = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    # FastAPI 的请求可能由不同线程处理，SQLite 需关闭同线程限制。
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """为每个请求创建独立数据库会话，并在请求结束时关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
