"""SQLAlchemy 数据模型。"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    """Python 选择、判断或填空题。"""

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("answer IN ('A', 'B', 'C', 'D')", name="ck_questions_answer"),
        CheckConstraint(
            "question_type IN ('single_choice', 'true_false', 'fill_blank')",
            name="ck_questions_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(String(1), nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="single_choice", server_default="single_choice"
    )
    # 填空题可有多个等价答案，使用 JSON 数组存储；其他题型为空。
    accepted_answers: Mapped[str | None] = mapped_column(Text, nullable=True)


class AppMetadata(Base):
    """记录内置题库版本，部署新版本时只替换旧的内置题。"""

    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    """使用用户名登录的学习账号。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AnswerRecord(Base):
    """账号的每一次答题记录，用于跨设备恢复学习进度。"""

    __tablename__ = "answer_records"
    __table_args__ = (
        Index("ix_answer_records_user_question", "user_id", "question_id"),
        Index("ix_answer_records_user_answered", "user_id", "answered_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
