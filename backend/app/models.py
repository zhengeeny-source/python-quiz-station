"""SQLAlchemy 数据模型。"""

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    """Python 单选题。"""

    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("answer IN ('A', 'B', 'C', 'D')", name="ck_questions_answer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(String(1), nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)

