"""首次启动时写入完整的分阶段题库。"""

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.models import Question
from app.question_bank import generate_question_bank


def seed_questions(db: Session) -> None:
    """仅在空题库中加入演示题，避免每次启动重复插入。"""
    count = db.scalar(select(func.count()).select_from(Question)) or 0
    if count:
        return

    # 批量插入比逐条 add 更适合 10,000 道初始题。
    db.execute(insert(Question), generate_question_bank())
    db.commit()
