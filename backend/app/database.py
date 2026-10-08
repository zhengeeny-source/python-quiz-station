"""数据库连接与会话管理。"""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 本地开发可直接复制 .env.example 为 .env；云平台仍由环境变量覆盖。
load_dotenv()


def _database_url() -> str:
    """读取数据库地址，并补全云平台常见连接串的 SQLAlchemy 驱动名。"""
    url = os.getenv("DATABASE_URL", "sqlite:///./python_quiz.db")
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _database_url()

engine_options: dict = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    # FastAPI 的请求可能由不同线程处理，SQLite 需关闭同线程限制。
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def migrate_question_schema(target_engine=None) -> None:
    """为旧版 SQLite/PostgreSQL/MySQL 数据库补上混合题型字段。

    项目规模很小，暂不引入 Alembic；这里的两个 ALTER 均为可重复检查后执行。
    """
    active_engine = target_engine or engine
    inspector = inspect(active_engine)
    if "questions" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("questions")}
    with active_engine.begin() as connection:
        if "question_type" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE questions ADD COLUMN question_type "
                    "VARCHAR(20) NOT NULL DEFAULT 'single_choice'"
                )
            )
        if "accepted_answers" not in columns:
            connection.execute(
                text("ALTER TABLE questions ADD COLUMN accepted_answers TEXT")
            )


def get_db() -> Generator[Session, None, None]:
    """为每个请求创建独立数据库会话，并在请求结束时关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
