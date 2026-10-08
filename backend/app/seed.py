"""写入并按版本升级内置题库。"""

from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session

from app.models import AppMetadata, Question
from app.question_bank import QUESTION_BANK_VERSION, generate_question_bank


def seed_questions(db: Session) -> None:
    """题库版本变化时原位更新内置题，保留题目 ID、答题记录和手工题。"""
    version_row = db.get(AppMetadata, "question_bank_version")
    if version_row and version_row.value == QUESTION_BANK_VERSION:
        return

    generated = generate_question_bank()
    existing_ids = dict(
        db.execute(
            select(Question.title, Question.id).where(Question.title.like("【阶段 %"))
        ).all()
    )
    updates: list[dict[str, object]] = []
    inserts: list[dict[str, object]] = []
    for question in generated:
        question_id = existing_ids.get(str(question["title"]))
        if question_id is None:
            inserts.append(question)
        else:
            updates.append({"id": question_id, **question})

    # 以题干匹配并原位更新，外键指向的 question_id 不变，因此用户进度不会丢失。
    if updates:
        db.execute(update(Question), updates)
    if inserts:
        db.execute(insert(Question), inserts)
    if version_row is None:
        db.add(AppMetadata(key="question_bank_version", value=QUESTION_BANK_VERSION))
    else:
        version_row.value = QUESTION_BANK_VERSION
    db.commit()
