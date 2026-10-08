"""写入并按版本升级内置题库。"""

from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from app.models import AppMetadata, Question
from app.question_bank import QUESTION_BANK_VERSION, generate_question_bank


def seed_questions(db: Session) -> None:
    """题库版本变化时替换内置题，保留不带阶段前缀的手工录入题。"""
    version_row = db.get(AppMetadata, "question_bank_version")
    if version_row and version_row.value == QUESTION_BANK_VERSION:
        return

    # 内置题都有阶段前缀；管理员手工录入的普通题目不会被删除。
    db.execute(delete(Question).where(Question.title.like("【阶段 %")))
    db.execute(insert(Question), generate_question_bank())
    if version_row is None:
        db.add(AppMetadata(key="question_bank_version", value=QUESTION_BANK_VERSION))
    else:
        version_row.value = QUESTION_BANK_VERSION
    db.commit()
