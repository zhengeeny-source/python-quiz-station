"""登录账号的累计学习统计与答题历史。"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnswerRecord, Question, User
from app.schemas import AnswerHistoryItem, ProgressSummary
from app.security import get_current_user


router = APIRouter(prefix="/api/progress", tags=["progress"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/summary", response_model=ProgressSummary)
def summary(user: CurrentUser, db: DbSession) -> ProgressSummary:
    row = db.execute(
        select(
            func.count(AnswerRecord.id),
            func.coalesce(func.sum(case((AnswerRecord.is_correct.is_(True), 1), else_=0)), 0),
            func.count(distinct(AnswerRecord.question_id)),
        ).where(AnswerRecord.user_id == user.id)
    ).one()
    total, correct, unique_questions = map(int, row)
    return ProgressSummary(
        total_answered=total,
        correct_count=correct,
        wrong_count=total - correct,
        accuracy=round(correct / total * 100) if total else 0,
        unique_questions=unique_questions,
    )


@router.get("/history", response_model=list[AnswerHistoryItem])
def history(
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AnswerHistoryItem]:
    rows = db.execute(
        select(AnswerRecord, Question)
        .join(Question, Question.id == AnswerRecord.question_id)
        .where(AnswerRecord.user_id == user.id)
        .order_by(AnswerRecord.answered_at.desc(), AnswerRecord.id.desc())
        .limit(limit)
    ).all()
    return [
        AnswerHistoryItem(
            id=record.id,
            question_id=record.question_id,
            title=question.title,
            question_type=question.question_type,
            selected_answer=record.selected_answer,
            is_correct=record.is_correct,
            answered_at=record.answered_at,
        )
        for record, question in rows
    ]
